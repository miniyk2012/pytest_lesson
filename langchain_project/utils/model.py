import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI


def check_deepseek_api_key():
    print("\n--- 检查 DeepSeek API 密钥 ---")
    # 加载环境变量
    load_dotenv()

    # 配置 DeepSeek API 密钥
    openai_api_key = os.getenv("DEEPSEEK_API_KEY")
    if not openai_api_key:
        raise ValueError("DEEPSEEK_API_KEY not found in environment variables. Please set it in a .env file.")

    print("  - 找到了 DEEPSEEK_API_KEY 环境变量。")
    # 为了安全，我们只显示密钥的开头和结尾
    print(f"    (Key: {openai_api_key[:5]}...{openai_api_key[-4:]})")
    return True


def init_model(callbacks=None):
    check_deepseek_api_key()
    # 2. 定义模型
    llm = init_chat_model("deepseek-chat", model_provider="deepseek", callbacks=callbacks)
    return llm


def init_openai_model(callbacks=None):
    """仍然是加载deepseek模型, 因为设置了OPENAI_BASE_URL=https://api.deepseek.com"""
    check_deepseek_api_key()
    model = ChatOpenAI(model_name="deepseek-chat", callbacks=callbacks)
    return model
