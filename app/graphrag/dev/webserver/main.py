import logging
import os
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from graphrag.query.context_builder.conversation_history import ConversationHistory
from graphrag.query.question_gen.local_gen import LocalQuestionGen
from graphrag.query.structured_search.basic_search.search import BasicSearch
from graphrag.query.structured_search.drift_search.search import DRIFTSearch
from graphrag.query.structured_search.global_search.search import GlobalSearch
from graphrag.query.structured_search.local_search.search import LocalSearch
from jinja2 import Template
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionMessage, ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice, ChoiceDelta

from webserver import gtypes
from webserver import search
from webserver import utils
from webserver.configs import settings
from webserver.utils import consts

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="webserver/static"), name="static")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


basic_search: BasicSearch
local_search: LocalSearch
global_search: GlobalSearch
drift_search: DRIFTSearch
question_gen: LocalQuestionGen


@app.on_event("startup")
async def startup_event():
    """
    服务启动时的初始化函数，使用 FastAPI 的 @app.on_event("startup") 装饰器
    加载配置和数据，初始化各种搜索引擎（local_search, global_search, drift_search, basic_search）
    这是实现秒级响应的关键之一：服务启动时就预加载所有数据和模型，而不是每次请求时加载
    """
    global local_search
    global global_search
    global question_gen
    global drift_search
    global basic_search
    root = Path(settings.root).resolve()
    data_dir = Path(settings.data).resolve()
    config, data = await search.load_context(root, data_dir)
    local_search = await search.load_local_search_engine(config, data)
    global_search = await search.load_global_search_engine(config, data)
    drift_search = await search.load_drift_search_engine(config, data)
    basic_search = await search.load_basic_search_engine(config, data)
    # question_gen = await search.build_local_question_gen(llm, token_encoder=token_encoder)


@app.get("/")
async def index():
    """
    主页路由，返回静态页面
    """
    html_file_path = os.path.join("webserver", "templates", "index.html")
    with open(html_file_path, "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)


async def handle_sync_response(request, search, conversation_history):
    """
    处理同步响应的函数，使用 FastAPI 的 @app.post("/v1/chat/completions") 装饰器
    接收 ChatCompletionRequest 请求，并返回 ChatCompletion 响应
    """
    result = await search.asearch(request.messages[-1].content, conversation_history=conversation_history)
    if isinstance(search, DRIFTSearch):
        response = result.response
        response = response["nodes"][0]["answer"]
    else:
        response = result.response

    reference = utils.get_reference(response)
    if reference:
        response += f"\n{utils.generate_ref_links(reference, request.model)}"
    from openai.types.chat.chat_completion import Choice
    completion = ChatCompletion(
        id=f"chatcmpl-{uuid.uuid4().hex}",
        created=int(time.time()),
        model=request.model,
        object="chat.completion",
        choices=[
            Choice(
                index=0,
                finish_reason="stop",
                message=ChatCompletionMessage(
                    role="assistant",
                    content=response
                )
            )
        ],
        usage=CompletionUsage(
            completion_tokens=-1,
            prompt_tokens=result.prompt_tokens,
            total_tokens=-1
        )
    )
    return JSONResponse(content=jsonable_encoder(completion))


async def handle_stream_response(request, search, conversation_history):
    """
    处理流式响应的函数，使用 FastAPI 的 @app.post("/v1/chat/completions") 装饰器
    接收 ChatCompletionRequest 请求，并返回 ChatCompletion 响应
    """
    async def wrapper_astream_search():
        token_index = 0
        chat_id = f"chatcmpl-{uuid.uuid4().hex}"
        full_response = ""
        async for token in search.astream_search(request.messages[-1].content, conversation_history):  # 调用原始的生成器
            if token_index == 0:
                token_index += 1
                continue

            chunk = ChatCompletionChunk(
                id=chat_id,
                created=int(time.time()),
                model=request.model,
                object="chat.completion.chunk",
                choices=[
                    Choice(
                        index=token_index - 1,
                        finish_reason=None,
                        delta=ChoiceDelta(
                            role="assistant",
                            content=token
                        )
                    )
                ]
            )
            yield f"data: {chunk.json()}\n\n"
            token_index += 1
            full_response += token

        content = ""
        reference = utils.get_reference(full_response)
        if reference:
            content = f"\n{utils.generate_ref_links(reference, request.model)}"
        finish_reason = 'stop'
        chunk = ChatCompletionChunk(
            id=chat_id,
            created=int(time.time()),
            model=request.model,
            object="chat.completion.chunk",
            choices=[
                Choice(
                    index=token_index,
                    finish_reason=finish_reason,
                    delta=ChoiceDelta(
                        role="assistant",
                        # content=result.context_data["entities"].head().to_string()
                        content=content
                    )
                ),
            ],
        )
        yield f"data: {chunk.json()}\n\n"
        yield f"data: [DONE]\n\n"

    return StreamingResponse(wrapper_astream_search(), media_type="text/event-stream")


@app.post("/v1/chat/completions")
async def chat_completions(request: gtypes.ChatCompletionRequest):
    if not local_search or not global_search or not drift_search or not basic_search:
        logger.error("search engines is not initialized")
        raise HTTPException(status_code=500, detail="search engines is not initialized")

    try:
        history = request.messages[:-1]
        conversation_history = ConversationHistory.from_list([message.dict() for message in history])

        if request.model == consts.INDEX_GLOBAL:
            search_engine = global_search
        elif request.model == consts.INDEX_LOCAL:
            search_engine = local_search
        elif request.model == consts.INDEX_DRIFT:
            search_engine = drift_search
        else:
            search_engine = basic_search

        if not request.stream:
            return await handle_sync_response(request, search_engine, conversation_history)
        else:
            return await handle_stream_response(request, search_engine, conversation_history)
    except Exception as e:
        logger.error(msg=f"chat_completions error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/advice_questions", response_model=gtypes.QuestionGenResult)
async def get_advice_question(request: gtypes.ChatQuestionGen):
    raise NotImplementedError("get_advice_question is not implemented since version 1.1.2")
    if request.model == consts.INDEX_LOCAL:
        local_context = await switch_context(index=request.model)
        question_gen.context_builder = local_context
    else:
        raise NotImplementedError(f"model {request.model} is not supported")
    question_history = [message.content for message in request.messages if message.role == "user"]
    candidate_questions = await question_gen.agenerate(
        question_history=question_history, context_data=None, question_count=5
    )
    # the original generated question is "- what about xxx?"
    questions: list[str] = [question.removeprefix("-").strip() for question in candidate_questions.response]
    resp = gtypes.QuestionGenResult(questions=questions,
                                    completion_time=candidate_questions.completion_time,
                                    llm_calls=candidate_questions.llm_calls,
                                    prompt_tokens=candidate_questions.prompt_tokens)
    return resp




@app.get("/v1/references/{index_id}/{datatype}/{id}", response_class=HTMLResponse)
async def get_reference(index_id: str, datatype: str, id: int):
    if not os.path.exists(settings.data):
        raise HTTPException(status_code=404, detail=f"{index_id} not found")
    if datatype not in ["entities", "claims", "sources", "reports", "relationships"]:
        raise HTTPException(status_code=404, detail=f"{datatype} not found")

    data = await search.get_index_data(settings.data, datatype, id)
    html_file_path = os.path.join("webserver", "templates", f"{datatype}_template.html")
    with open(html_file_path, 'r') as file:
        html_content = file.read()
    template = Template(html_content)
    html_content = template.render(data=data)
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=settings.server_port)
