"""
测试工具调用功能
"""
from harness.tools.calculator import InsuranceCalculator, ClauseRetriever


def test_insurance_calculator():
    """测试保险计算器"""
    print("="*60)
    print("🧮 测试：保险计算器")
    print("="*60)

    calc = InsuranceCalculator()

    # 测试1：保费计算
    print("\n【测试1】保费计算")
    print("输入：30岁男性，50万保额，20年缴费")

    result = calc.calculate_premium(
        coverage_amount=500000,
        age=30,
        gender="male",
        payment_period=20
    )

    print(f"\n结果：")
    print(f"  保额：¥{result['coverage_amount']:,}")
    print(f"  年缴保费：¥{result['annual_premium']:,}")
    print(f"  总保费：¥{result['total_premium']:,}")

    # 测试2：收益估算
    print("\n【测试2】收益估算")
    print("输入：年缴10,000元，20年保险期间")

    returns = calc.estimate_returns(
        premium=10000,
        years=20,
        expected_rate=0.035
    )

    print(f"\n结果：")
    print(f"  总保费：¥{returns['total_premium']:,}")
    print(f"  预期终值：¥{returns['expected_final_value']:,}")
    print(f"  预期收益：¥{returns['expected_gain']:,}")
    print(f"  预期收益率：{returns['expected_rate']*100}%")
    print(f"  ⚠️  {returns['disclaimer']}")


def test_clause_retriever():
    """测试条款检索器"""
    print("\n" + "="*60)
    print("📋 测试：条款检索器")
    print("="*60)

    retriever = ClauseRetriever()

    # 测试1：检索等待期条款
    print("\n【测试1】检索 '等待期'")
    result = retriever.search_clause("等待期", "life")
    print(f"\n结果：")
    for clause in result['matched_clauses']:
        print(f"  条款：{clause['条款']}")
        print(f"  内容：{clause['内容']}")

    # 测试2：检索豁免条款
    print("\n【测试2】检索 '豁免'")
    result = retriever.search_clause("豁免", "life")
    print(f"\n结果：")
    for clause in result['matched_clauses']:
        print(f"  条款：{clause['条款']}")
        print(f"  内容：{clause['内容']}")


def test_guardrails():
    """测试合规拦截"""
    print("\n" + "="*60)
    print("🛡️  测试：Guardrails 合规拦截")
    print("="*60)

    from harness.guardrails import Guardrails

    guardrails = Guardrails()

    test_cases = [
        ("我想买保险", True, "正常输入"),
        ("这个产品收益率多少", True, "正常咨询"),
        ("这个产品保本保息吗", False, "夸大表述"),
        ("有没有内幕消息", False, "敏感词"),
    ]

    print("\n测试结果：")
    for input_text, should_pass, desc in test_cases:
        result = guardrails.check_input(input_text)
        status = "✓ 通过" if result["allowed"] else "✗ 拦截"
        expected = "✓" if result["allowed"] == should_pass else "✗"
        print(f"\n{expected} {desc}")
        print(f"   输入：'{input_text}'")
        print(f"   结果：{status}")
        if not result["allowed"]:
            print(f"   原因：{result['reason']}")


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🔧 保险 Agent 工具测试")
    print("="*60)

    test_insurance_calculator()
    test_clause_retriever()
    test_guardrails()

    print("\n" + "="*60)
    print("✅ 所有工具测试完成！")
    print("="*60)


if __name__ == "__main__":
    main()
