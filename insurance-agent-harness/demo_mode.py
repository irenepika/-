"""
保险 Agent 演示模式（不需要真实 API Key）
演示系统架构和组件交互
"""
import asyncio
import json
from datetime import datetime


class MockSalesActor:
    """模拟销售 Actor（不调用真实 API）"""

    def generate_response(self, user_input, user_profile, conversation_history, available_tools):
        # 模拟回复生成逻辑
        responses = {
            "default": "感谢您的咨询！我是您的专属保险顾问。根据您的需求，我推荐我们的重疾险产品，它可以为您提供全面的健康保障。",
            "premium": "根据您提供的信息，我已经为您计算了保费。30岁男性，50万保额，20年缴费，年缴保费约 3500 元。",
            "risk": "关于收益，我需要向您说明：保险产品的收益是不保证的，实际收益取决于保险公司的经营状况。投资有风险，购买需谨慎。",
        }

        if "保费" in user_input or "多少" in user_input:
            return responses["premium"]
        elif "收益" in user_input or "风险" in user_input:
            return responses["risk"]
        else:
            return responses["default"]


class MockIntentClassifier:
    """模拟意图分类器"""

    def classify_conversation_window(self, conversation_window, previous_state):
        # 模拟状态判定
        return {
            "customer_temperature": "warm",
            "funnel_stage": "interest",
            "confidence": 0.85,
            "reasoning": "用户主动询问产品详情，表现出明确的兴趣"
        }


class MockMemory:
    """模拟内存管理器"""

    def __init__(self):
        self.profiles = {}
        self.states = {}
        self.history = {}

    async def get_user_profile(self, user_id):
        if user_id not in self.profiles:
            self.profiles[user_id] = {
                "user_id": user_id,
                "disc_type": "I",
                "interaction_stage": "awareness"
            }
        return self.profiles[user_id]

    async def get_conversation_history(self, user_id):
        return self.history.get(user_id, [])

    async def get_current_state(self, user_id):
        return self.states.get(user_id, {
            "customer_temperature": "neutral",
            "funnel_stage": "awareness"
        })

    async def append_conversation_turn(self, user_id, user_message, assistant_message, session_id=None):
        if user_id not in self.history:
            self.history[user_id] = []
        self.history[user_id].extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message}
        ])

    async def update_state(self, user_id, new_state):
        if user_id not in self.states:
            self.states[user_id] = {}
        self.states[user_id].update(new_state)


class DemoAgentCore:
    """演示版 Agent 核心"""

    def __init__(self):
        self.sales_actor = MockSalesActor()
        self.intent_classifier = MockIntentClassifier()
        self.memory = MockMemory()

    async def chat(self, user_id, user_input, session_id=None):
        print(f"\n{'='*60}")
        print(f"📞 用户输入: {user_input}")
        print(f"{'='*60}")

        # Step 1: 获取用户画像
        print("\n⚙️  [Step 1] 从 Memory 拉取用户画像...")
        user_profile = await self.memory.get_user_profile(user_id)
        print(f"   ✓ DISC 类型: {user_profile['disc_type']}")
        print(f"   ✓ 互动阶段: {user_profile['interaction_stage']}")

        # Step 2: Guardrails 检查（演示中总是通过）
        print("\n🛡️  [Step 2] Guardrails 合规检查...")
        print(f"   ✓ 输入合规，允许通过")

        # Step 3: 生成回复
        print("\n🤖 [Step 3] Sales Actor 生成回复...")
        conversation_history = await self.memory.get_conversation_history(user_id)
        response = self.sales_actor.generate_response(
            user_input,
            user_profile,
            conversation_history,
            []
        )
        print(f"   ✓ 回复已生成")

        # Step 4: 更新对话历史
        print("\n💾 [Step 4] 更新对话历史到 Memory...")
        await self.memory.append_conversation_turn(user_id, user_input, response)
        print(f"   ✓ 历史已保存")

        # Step 5: 异步状态更新（模拟）
        print("\n🔄 [Step 5] 异步状态更新（后台执行）...")
        recent_window = await self.memory.get_conversation_history(user_id)
        current_state = await self.memory.get_current_state(user_id)
        new_state = self.intent_classifier.classify_conversation_window(
            recent_window[-5:],
            current_state
        )
        await self.memory.update_state(user_id, new_state)
        print(f"   ✓ 客户温度: {current_state['customer_temperature']} → {new_state['customer_temperature']}")
        print(f"   ✓ 漏斗阶段: {current_state['funnel_stage']} → {new_state['funnel_stage']}")

        # 返回结果
        current_state = await self.memory.get_current_state(user_id)

        return {
            "response": response,
            "user_id": user_id,
            "current_disc_type": user_profile['disc_type'],
            "current_temperature": current_state['customer_temperature'],
            "current_funnel_stage": current_state['funnel_stage'],
            "timestamp": datetime.utcnow().isoformat()
        }


async def run_demo():
    """运行演示"""
    print("\n" + "="*60)
    print("🎯 保险 Agent Harness - 演示模式")
    print("="*60)
    print("\n💡 这是演示模式，不需要真实的 OpenAI API Key")
    print("   展示系统的架构和组件交互流程\n")

    agent = DemoAgentCore()

    # 测试场景
    scenarios = [
        {
            "user_id": "demo_user_001",
            "input": "你好，我想了解一下保险产品",
            "desc": "场景1：初始咨询"
        },
        {
            "user_id": "demo_user_001",
            "input": "我对重疾险比较感兴趣，30岁男性，保额50万，保费大概多少？",
            "desc": "场景2：产品咨询（含保费计算）"
        },
        {
            "user_id": "demo_user_001",
            "input": "这个产品的收益率怎么样？有没有风险？",
            "desc": "场景3：合规性测试（风险提示）"
        }
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'#'*60}")
        print(f"# {scenario['desc']}")
        print(f"{'#'*60}")

        result = await agent.chat(
            user_id=scenario['user_id'],
            user_input=scenario['input']
        )

        print(f"\n{'='*60}")
        print(f"📊 Agent 回复:")
        print(f"{'='*60}")
        print(f"{result['response']}\n")

        print(f"📈 当前状态:")
        print(f"   - DISC 类型: {result['current_disc_type']}")
        print(f"   - 客户温度: {result['current_temperature']}")
        print(f"   - 漏斗阶段: {result['current_funnel_stage']}")

        await asyncio.sleep(0.5)  # 暂停以便观察

    print("\n" + "="*60)
    print("✅ 演示完成！")
    print("="*60)
    print("\n📝 系统架构演示:")
    print("   ✓ 实时对话链路: 用户输入 → 画像 → 检查 → 生成 → 保存")
    print("   ✓ 异步状态更新: 后台分析客温和漏斗状态")
    print("   ✓ 防幻觉设计: Pydantic 强类型 + 审计日志")
    print("\n💡 要使用真实 API，请设置环境变量 OPENAI_API_KEY")


if __name__ == "__main__":
    asyncio.run(run_demo())
