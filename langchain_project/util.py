from dotenv import load_dotenv
import os


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

def main():
    """
    这是一个简单的脚本，用于验证 LangChain 及其相关包是否已正确安装，
    并检查关键的环境变量是否已设置。
    """
    print("--- LangChain 安装与环境检查 ---")

    # 1. 检查 python-dotenv 包的导入
    try:
        from dotenv import load_dotenv
        print("\n[SUCCESS] `python-dotenv` 包导入成功。")
    except ImportError as e:
        print(f"\n[ERROR] `python-dotenv` 包导入失败: {e}")
        print("请运行: uv add python-dotenv")
        return

    # 2. 检查 LangChain 包的导入
    try:
        import langchain
        from langchain.prompts import PromptTemplate
        from langchain.schema import BaseMessage
        print(f"\n[SUCCESS] `langchain` 包导入成功。版本: {langchain.__version__}")
    except ImportError as e:
        print(f"\n[ERROR] `langchain` 包导入失败: {e}")
        print("请运行: uv add langchain")
        return

    # 3. 检查 OpenAI 集成包的导入和 API 密钥
    try:
        from langchain_deepseek import ChatDeepSeek
        print("[SUCCESS] `langchain-openai` 包导入成功。")

        # 调用专门的 API 密钥检查函数
        check_deepseek_api_key()

        # 检查 API Base URL (可选)
        api_base = os.getenv("DEEPSEEK_API_BASE")
        if api_base:
            print(f"  - 找到了 DEEPSEEK_API_BASE 环境变量: {api_base}")
        else:
            print("  - [INFO] 未设置 DEEPSEEK_API_BASE 环境变量。")
            print("    这是可选的，如果需要使用自定义 DeepSeek API 端点，")
            print("    请在 .env 文件中添加: DEEPSEEK_API_BASE=\"https://your-custom-endpoint.com/v1\"")

    except ImportError as e:
        print(f"\n[WARNING] `langchain-deepseek` 包未安装或导入失败: {e}")
        print("如果需要使用 DeepSeek 模型，请运行: uv add langchain-deepseek")

    print("\n--- 检查完成 ---")
    print("环境基本配置完毕。您可以开始学习 LangChain 的其他章节了！")


if __name__ == "__main__":
    main()
