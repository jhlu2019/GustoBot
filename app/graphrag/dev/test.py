import openai


# 这是第一种 显式设置api_key的方式
api_key = "sk-proj-1234567890"

client = openai.OpenAI(api_key=api_key)



import os

# 这是第二种 通过环境变量设置api_key的方式
api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=api_key)



from openai import OpenAI

client = OpenAI(api_key=api_key)
