from typing import List, Dict, AsyncGenerator, Optional, Callable, Sequence, Any, TYPE_CHECKING
import json
import asyncio
from gustobot.tools import get_tool, list_openai_tools, list_tool_specs
from openai import AsyncOpenAI
from gustobot.config import settings
from gustobot.infrastructure.core.logger import get_logger
from gustobot.application.prompts.search_prompts import SEARCH_SYSTEM_PROMPT, SEARCH_SUMMARY_PROMPT
from datetime import datetime

if TYPE_CHECKING:
    from openai.types.chat import (
        ChatCompletionChoice,
        ChatCompletionMessageParam,
    )
else:
    ChatCompletionChoice = Any  # type: ignore
    ChatCompletionMessageParam = Dict[str, Any]  # type: ignore

logger = get_logger(service="search")

class SearchService:
    def __init__(self):
        logger.info("Initializing SearchService...")
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=(settings.OPENAI_API_BASE or "").rstrip("/") or None,
        )
        self.model = settings.OPENAI_MODEL
        self.search_tool = get_tool("search")

        self._tool_specs = list_tool_specs()
        self._openai_tools = list_openai_tools()

        self.tools_description = self._generate_tools_description()

    def _generate_tools_description(self) -> str:
        """根据工具定义生成工具描述提示"""
        tool_descriptions = []

        for spec in self._tool_specs:
            name = spec["name"]
            desc = spec.get("description", "")
            params = []

            param_schema = spec.get("parameters", {})
            required_params = param_schema.get("required", [])
            properties = param_schema.get("properties", {})

            for param_name in required_params:
                param_info = properties.get(param_name, {})
                param_desc = param_info.get("description", "")
                if param_desc:
                    params.append(f"{param_name}，作用是：{param_desc}")

            tool_desc = (
                f"{name}，{desc}"
                f"{'，必须解析出来的参数是：' if params else ''}"
                f"{', '.join(params)}"
            )
            tool_descriptions.append(tool_desc)

        return (
            "你现在可用的工具有：\n\n" + 
            "\n".join(tool_descriptions)
        )

    async def _call_with_tool(
        self,
        messages: Sequence["ChatCompletionMessageParam"],
    ) -> "ChatCompletionChoice":
        """调用模型并获取工具调用结果"""
        try:
            logger.info("Calling model for tool selection.")
            logger.debug(f"Messages: {messages}")
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=list(messages),
                tools=self._openai_tools,
                tool_choice="auto"  # 让模型自己决定是否使用工具
            )
            
            logger.info(f"Model response: {response.choices[0]}")
            return response.choices[0]
            
        except Exception as e:
            logger.error(f"Error in _call_with_tool: {str(e)}", exc_info=True)
            raise

    async def generate_stream(
        self, 
        query: str,
        user_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
        on_complete: Optional[Callable] = None
    ) -> AsyncGenerator[str, None]:
        """流式生成带搜索功能的回复"""
        try:
            logger.info(f"Starting search generation for query: {query}")
            
            # 使用格式化的系统提示
            messages = [
                {
                    "role": "system",
                    "content": SEARCH_SYSTEM_PROMPT.format(
                        tools_description=self.tools_description
                    )
                },
                {
                    "role": "user",
                    "content": query
                }
            ]

            # 第一步：获取工具调用
            choice = await self._call_with_tool(messages)
            logger.info(f"Tool call response: {choice}")
            
            # 根据finish_reason决定处理方式
            if choice.finish_reason == "tool_calls":
                # 需要搜索的情况
                tool_calls = choice.message.tool_calls
                if tool_calls:
                    tool_call = tool_calls[0]
                    logger.info(f"Processing tool call: {tool_call}")
                    
                    try:
                        arguments = json.loads(tool_call.function.arguments or "{}")
                        search_query = arguments.get("query", "")
                        num_results = arguments.get("num_results")

                        if not search_query:
                            logger.warning("Tool call missing 'query' argument; skipping execution.")
                            search_results = []
                        else:
                            search_results = await asyncio.to_thread(
                                self.search_tool.search,
                                search_query,
                                num_results=num_results,
                            )

                        logger.info(f"Got {len(search_results)} search results")
                        
                        if search_results:
                            # 构建上下文内容
                            context = []
                            for result in search_results:
                                context.append(
                                    f"来源：{result['title']}\n"
                                    f"链接：{result['url']}\n"
                                    f"内容：{result['snippet']}\n"
                                )
                            
                            # 构造带上下文的提示
                            context_prompt = SEARCH_SUMMARY_PROMPT.format(
                                context="\n---\n".join(context),
                                query=query,
                                cur_date=datetime.now().strftime("%Y年%m月%d日")
                            )
                            
                            # 先返回一个类型标识，告诉前端这是搜索结果
                            yield f"data: {json.dumps({'type': 'search_start'}, ensure_ascii=False)}\n\n"
                            
                            # 返回搜索结果
                            search_data = {
                                "type": "search_results",  # 保持原有的类型标识
                                "total": len(search_results),
                                "query": search_query,
                                "results": [
                                    {
                                        "title": result["title"],
                                        "url": result["url"],
                                        "snippet": result["snippet"]
                                    }
                                    for result in search_results
                                ]
                            }
                            yield f"data: {json.dumps(search_data, ensure_ascii=False)}\n\n"
                            
                            # 使用新的消息上下文生成回复
                            async for chunk in await self.client.chat.completions.create(
                                model=self.model,
                                messages=[
                                    {"role": "system", "content": context_prompt}
                                ],
                                stream=True
                            ):      

                                if chunk.choices[0].delta.content:
                                    content = json.dumps(chunk.choices[0].delta.content, ensure_ascii=False)
                                    yield f"data: {content}\n\n"
             
                    except Exception as e:
                        logger.error(f"Failed to execute tool call: {e}", exc_info=True)
                
            elif choice.finish_reason == "stop":
                # 直接回答的情况，使用流式响应
                logger.info("Model chose to answer directly, streaming response...")
                
                # 先返回一个类型标识，告诉前端这是直接回答
                yield f"data: {json.dumps({'type': 'direct_answer'}, ensure_ascii=False)}\n\n"
                
                # 使用流式API重新生成回答
                stream_response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True
                )
                
                full_response = []
                async for chunk in stream_response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response.append(content)
                        # 包装直接回答的内容
                        direct_payload = {
                            "type": "direct_content",
                            "content": content,
                        }
                        yield f"data: {json.dumps(direct_payload, ensure_ascii=False)}\n\n"
                
                # 如果需要保存对话
                if on_complete and user_id is not None and conversation_id is not None:
                    complete_response = "".join(full_response)
                    await on_complete(user_id, conversation_id, [{"role": "user", "content": query}], complete_response)
                
        except Exception as e:
            logger.error(f"Error in generate_stream: {str(e)}", exc_info=True)
            raise
