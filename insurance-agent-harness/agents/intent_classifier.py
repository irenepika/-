"""
Intent Classifier - 意图与状态分类器
在后台异步识别客户温度变化与漏斗状态
"""
from typing import Literal
from openai import OpenAI
from schemas.state_models import CustomerTemperature, FunnelStage


class IntentClassifier:
    """
    后台判别器：根据滑动窗口识别"客温(冷/暖)"与当前漏斗状态
    使用 GPT-4o-mini 以实现低成本、高频率的后台分析
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = OpenAI()
        self.model = model

    def classify_conversation_window(
        self,
        conversation_window: list[dict],
        previous_state: dict
    ) -> dict:
        """
        分析最近的对话窗口，提取状态变化

        Args:
            conversation_window: 最近 N 轮对话（如最近 3-5 轮）
            previous_state: 上一轮的状态（温度、阶段等）

        Returns:
            包含 customer_temperature 和 funnel_stage 的状态字典
        """
        conversation_text = self._format_conversation(conversation_window)

        prompt = f"""你是一个专业的销售对话分析师。请分析以下对话，提取关键信息。

【最近对话】
{conversation_text}

【上一轮状态】
- 客户温度：{previous_state.get('customer_temperature', 'unknown')}
- 漏斗阶段：{previous_state.get('funnel_stage', 'unknown')}

【任务】
请判断：
1. 客户温度（Customer Temperature）：cold/neutral/warm/hot
   - cold: 客户表现出抗拒、冷淡、不耐烦
   - neutral: 中性态度，无明显情绪倾向
   - warm: 表现出兴趣，愿意继续交流
   - hot: 高度认可，准备购买或已表达购买意向

2. 漏斗阶段（Funnel Stage）：awareness/interest/consideration/intent/evaluation/purchase
   - awareness: 初始接触，了解保险概念
   - interest: 对产品表现出兴趣
   - consideration: 开始对比和思考具体方案
   - intent: 明确表达购买意愿
   - evaluation: 讨论细节、条款、价格
   - purchase: 准备签约或已签约

请以 JSON 格式返回，格式为：
{{
    "customer_temperature": "温度",
    "funnel_stage": "阶段",
    "confidence": 0.95,
    "reasoning": "简要理由"
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是销售对话分析专家，输出严格的 JSON 格式。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        import json
        result = json.loads(response.choices[0].message.content or "{}")

        return {
            "customer_temperature": result.get("customer_temperature", "neutral"),
            "funnel_stage": result.get("funnel_stage", "awareness"),
            "confidence": result.get("confidence", 0.5),
            "reasoning": result.get("reasoning", "")
        }

    def _format_conversation(self, conversation_window: list[dict]) -> str:
        """将对话窗口格式化为易读文本"""
        formatted = []
        for turn in conversation_window:
            role = turn.get("role", "unknown")
            content = turn.get("content", "")
            role_name = {"user": "客户", "assistant": "顾问"}.get(role, role)
            formatted.append(f"{role_name}: {content}")
        return "\n\n".join(formatted)
