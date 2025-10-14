"""工具描述定义文件"""

SEARCH_TOOL = {
    "name": "search",
    "description": "使用谷歌搜索从互联网获取更多的实时信息",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "通过搜索从互联网获取的信息的问题、内容、关键词等"
            }
        },
        "required": ["query"]
    }
}

# # 可以添加更多工具定义
# WEATHER_TOOL = {
#     "name": "get_weather",
#     "description": "获取天气信息",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "city": {
#                 "type": "string",
#                 "description": "城市名称"
#             }
#         },
#         "required": ["city"]
#     }
# }

# 工具定义集合
TOOL_DEFINITIONS = {
    "search": SEARCH_TOOL,
    # "weather": WEATHER_TOOL
} 