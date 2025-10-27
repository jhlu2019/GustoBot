"""测试 LLM 重写功能"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# 添加项目路径
sys.path.insert(0, '/')

from app.clients.llm import LLMClient
from app.core.config import Config
from app.prompts.manager import PromptManager, SchemaColumn

def test_llm_basic():
    """测试 LLM 基础功能"""
    print("\n" + "="*60)
    print("测试 1: LLM 基础调用")
    print("="*60)

    # 创建配置
    config = Config()
    print(f"LLM Provider: {config.llm_provider}")
    print(f"LLM Model: {config.llm_model}")
    print(f"LLM Base URL: {config.llm_base_url}")
    print()

    # 创建 LLM 客户端
    llm_client = LLMClient(config)

    # 测试简单对话
    try:
        system_prompt = "你是一个专业的助手。"
        user_prompt = "请用一句话介绍什么是高新技术企业。"

        print(f"System Prompt: {system_prompt}")
        print(f"User Prompt: {user_prompt}")
        print()

        response = llm_client.generate(user_prompt, system_prompt)

        print("✅ LLM 调用成功")
        print(f"响应: {response}")
        return True

    except Exception as e:
        print(f"❌ LLM 调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_rewrite_with_prompt_manager():
    """测试使用 PromptManager 进行 LLM 重写"""
    print("\n" + "="*60)
    print("测试 2: 使用 PromptManager 进行数据重写")
    print("="*60)

    config = Config()
    llm_client = LLMClient(config)
    prompt_manager = PromptManager()

    # 模拟一条企业数据
    test_data = {
        "id": 1,
        "company_name": "苏州慧锐通智能科技有限公司",
        "credit_code": "91320508MA1MUDGL1E",
        "registered_capital": "1000万元",
        "establishment_date": "2018-05-20",
        "business_scope": "智能控制系统、物联网技术、人工智能技术的研发、销售；软件开发",
        "address": "江苏省苏州市高新区",
        "status": "在营"
    }

    # 定义 schema
    schema = [
        SchemaColumn(name="id", data_type="int", comment="企业ID"),
        SchemaColumn(name="company_name", data_type="varchar", comment="企业名称"),
        SchemaColumn(name="credit_code", data_type="varchar", comment="统一社会信用代码"),
        SchemaColumn(name="registered_capital", data_type="varchar", comment="注册资本"),
        SchemaColumn(name="establishment_date", data_type="date", comment="成立日期"),
        SchemaColumn(name="business_scope", data_type="text", comment="经营范围"),
        SchemaColumn(name="address", data_type="varchar", comment="地址"),
        SchemaColumn(name="status", data_type="varchar", comment="企业状态"),
    ]

    print("原始数据:")
    print("-" * 60)
    for key, value in test_data.items():
        print(f"  {key}: {value}")
    print()

    try:
        # 生成 prompt
        system_prompt, user_prompt = prompt_manager.get_prompt(
            table_name="企业信息",
            row_data=test_data,
            schema=schema,
        )

        print("生成的 System Prompt:")
        print("-" * 60)
        print(system_prompt)
        print()

        print("生成的 User Prompt:")
        print("-" * 60)
        print(user_prompt[:500] + "..." if len(user_prompt) > 500 else user_prompt)
        print()

        # 调用 LLM 重写
        print("调用 LLM 进行重写...")
        rewritten_content = llm_client.generate(user_prompt, system_prompt)

        print("\n✅ LLM 重写成功")
        print("="*60)
        print("重写后的内容:")
        print("-" * 60)
        print(rewritten_content)
        print("="*60)

        return True

    except Exception as e:
        print(f"❌ LLM 重写失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_rewrite_policy_data():
    """测试重写政策数据"""
    print("\n" + "="*60)
    print("测试 3: 重写政策数据")
    print("="*60)

    config = Config()
    llm_client = LLMClient(config)
    prompt_manager = PromptManager()

    # 模拟一条政策数据
    test_data = {
        "id": 1,
        "title": "关于推进我市生产性服务业高质量发展的若干政策",
        "content": "为贯彻落实《市政府办公厅关于加快发展生产性服务业促进产业结构调整升级的实施意见》，进一步推动我市生产性服务业高质量发展，特制定如下政策措施。一、支持研发设计服务。对新认定的国家级工业设计中心给予一次性奖励200万元。二、支持检验检测认证服务。对新获得CNAS认可的检验检测机构给予一次性奖励50万元。",
        "publish_date": "2023-06-15",
        "department": "市发改委",
        "policy_type": "产业政策"
    }

    schema = [
        SchemaColumn(name="id", data_type="int", comment="政策ID"),
        SchemaColumn(name="title", data_type="varchar", comment="政策标题"),
        SchemaColumn(name="content", data_type="text", comment="政策内容"),
        SchemaColumn(name="publish_date", data_type="date", comment="发布日期"),
        SchemaColumn(name="department", data_type="varchar", comment="发布部门"),
        SchemaColumn(name="policy_type", data_type="varchar", comment="政策类型"),
    ]

    print("原始政策数据:")
    print("-" * 60)
    print(f"标题: {test_data['title']}")
    print(f"内容: {test_data['content'][:100]}...")
    print()

    try:
        system_prompt, user_prompt = prompt_manager.get_prompt(
            table_name="policies",
            row_data=test_data,
            schema=schema,
        )

        print("调用 LLM 重写政策数据...")
        rewritten_content = llm_client.generate(user_prompt, system_prompt)

        print("\n✅ 政策数据重写成功")
        print("="*60)
        print("重写后的内容:")
        print("-" * 60)
        print(rewritten_content)
        print("="*60)

        return True

    except Exception as e:
        print(f"❌ 政策数据重写失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n🔍 开始测试 LLM 重写功能...")

    # 临时取消代理（避免访问内网服务器时出错）
    os.environ['http_proxy'] = ''
    os.environ['https_proxy'] = ''
    os.environ['all_proxy'] = ''

    results = {
        "LLM 基础调用": test_llm_basic(),
        "PromptManager 数据重写": test_llm_rewrite_with_prompt_manager(),
        "政策数据重写": test_llm_rewrite_policy_data(),
    }

    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:25s}: {status}")

    print("\n✨ 测试完成！")

    # 总结
    total = len(results)
    passed = sum(results.values())
    print(f"\n通过: {passed}/{total}")

    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
