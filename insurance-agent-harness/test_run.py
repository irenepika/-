"""
保险 Agent 测试运行脚本
演示完整的对话流程
"""
import asyncio
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from harness.core_loop import AgentCoreLoop
from harness.tools.registry import ToolRegistry
from harness.tools.calculator import register_default_tools


async def test_basic_conversation():
    """测试基础对话功能"""
    print("="*60)
    print("🚀 启动保险 Agent 测试")
    print("="*60)

    # 检查 API Key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your-openai-api-key-here":
        print("❌ 错误：请先设置 OPENAI_API_KEY 环境变量")
        print("   在 .env 文件中设置: OPENAI_API_KEY=your-actual-key")
        return

    # 初始化 Agent
    print("\n⚙️  初始化 Agent 组件...")
    tool_registry = ToolRegistry()
    register_default_tools(tool_registry)
    print(f"   ✓ 已注册 {len(tool_registry.tools)} 个工具")

    agent = AgentCoreLoop(tool_registry=tool_registry)
    print("   ✓ Agent 初始化完成")

    # 测试对话场景
    test_scenarios = [
        {
            "user_id": "test_user_001",
            "input": "你好，我想了解一下保险产品",
            "description": "初始咨询场景"
        },
        {
            "user_id": "test_user_001",
            "input": "我对重疾险比较感兴趣，30岁男性，保额50万，保费大概多少？",
            "description": "保费计算场景（触发工具调用）"
        },
        {
            "user_id": "test_user_001",
            "input": "这个产品的收益率怎么样？有没有风险？",
            "description": "合规性测试场景（需要风险提示）"
        }
    ]

    print("\n" + "="*60)
    print("📝 开始对话测试")
    print("="*60)

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n【测试 {i}】{scenario['description']}")
        print(f"用户: {scenario['input']}")

        try:
            result = await agent.chat(
                user_id=scenario['user_id'],
                user_input=scenario['input'],
                session_id=f"test_session_{i}"
            )

            if result.get("blocked"):
                print(f"⚠️  回复被拦截: {result.get('reason')}")
                print(f"系统消息: {result.get('response')}")
            else:
                print(f"Agent: {result['response']}")
                print(f"状态: DISC={result.get('current_disc_type')}, "
                      f"温度={result.get('current_temperature')}, "
                      f"阶段={result.get('current_funnel_stage')}")

        except Exception as e:
            print(f"❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()

        print("-" * 60)

    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)


async def test_guardrails():
    """测试合规拦截功能"""
    print("\n" + "="*60)
    print("🛡️  测试 Guardrails 合规拦截")
    print("="*60)

    from harness.guardrails import Guardrails

    guardrails = Guardrails()

    test_cases = [
        ("我想买保险", True, "正常输入"),
        ("这个产品收益率多少", True, "正常咨询"),
        ("我能得到内幕消息吗", False, "敏感词拦截"),
        ("这个产品保本保息吗", False, "夸大表述检测"),
    ]

    for input_text, should_pass, description in test_cases:
        result = guardrails.check_input(input_text)
        status = "✓" if result["allowed"] == should_pass else "✗"
        print(f"{status} {description}: '{input_text}'")
        if not result["allowed"]:
            print(f"   拦截原因: {result['reason']}")


async def test_tools():
    """测试工具功能"""
    print("\n" + "="*60)
    print("🔧 测试工具调用")
    print("="*60)

    from harness.tools.calculator import InsuranceCalculator, ClauseRetriever

    calc = InsuranceCalculator()
    retriever = ClauseRetriever()

    # 测试保费计算
    print("\n1. 保费计算测试:")
    premium_result = calc.calculate_premium(
        coverage_amount=500000,
        age=30,
        gender="male",
        payment_period=20
    )
    print(f"   保额: {premium_result['coverage_amount']} 元")
    print(f"   年缴保费: {premium_result['annual_premium']} 元")
    print(f"   总保费: {premium_result['total_premium']} 元")

    # 测试收益估算
    print("\n2. 收益估算测试:")
    returns_result = calc.estimate_returns(
        premium=10000,
        years=20
    )
    print(f"   总保费: {returns_result['total_premium']} 元")
    print(f"   预期终值: {returns_result['expected_final_value']} 元")
    print(f"   预期收益: {returns_result['expected_gain']} 元")
    print(f"   免责声明: {returns_result['disclaimer']}")

    # 测试条款检索
    print("\n3. 条款检索测试:")
    clause_result = retriever.search_clause("等待期", "life")
    print(f"   关键词: {clause_result['keyword']}")
    print(f"   匹配条款:")
    for clause in clause_result['matched_clauses']:
        print(f"   - {clause}")


async def main():
    """运行所有测试"""
    print("\n🎯 保险 Agent Harness - 测试运行\n")

    # 测试工具
    await test_tools()

    # 测试合规拦截
    await test_guardrails()

    # 测试完整对话
    await test_basic_conversation()

    print("\n" + "="*60)
    print("🎉 所有测试完成！")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
