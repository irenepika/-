"""
DISC Analyzer - DISC 性格分析器
长文本上下文压缩：将历史对话提炼为带证据的 DISC 报告
"""
from typing import Dict, Any, List
from openai import OpenAI


class DISCAnalyzer:
    """
    DISC 性格分析器：分析用户历史对话，提取性格特征
    使用长文本压缩技术，从大量对话中提炼关键证据
    """

    def __init__(self, model: str = "gpt-4o"):
        self.client = OpenAI()
        self.model = model

    def analyze_user(
        self,
        conversation_history: List[Dict[str, Any]],
        user_id: str
    ) -> Dict[str, Any]:
        """
        分析用户的 DISC 性格类型

        Args:
            conversation_history: 完整对话历史
            user_id: 用户 ID

        Returns:
            DISC 分析报告，包含：
            - disc_type: D/I/S/C 类型
            - confidence: 置信度
            - evidence: 支持该判断的证据（对话片段）
            - interaction_style: 互动风格建议
        """
        # 压缩长文本上下文
        compressed_context = self._compress_conversations(conversation_history)

        prompt = f"""你是一位专业的用户心理分析师。请根据以下对话历史，分析用户的 DISC 性格类型。

【用户 ID】{user_id}

【对话历史】
{compressed_context}

【DISC 类型说明】
- **D 型 (支配型 Dominance)**：直接、果断、结果导向
  特征：说话简短有力、关注效率和结果、不喜欢啰嗦、喜欢掌控对话节奏

- **I 型 (影响型 Influence)**：热情、互动、情感导向
  特征：表达丰富、爱讲故事、注重情感连接、容易被新颖事物吸引

- **S 型 (稳健型 Steadiness)**：温和、耐心、关系导向
  特征：说话温和、需要时间思考、重视安全感、不喜欢被催促

- **C 型 (谨慎型 Compliance)**：理性、细节、数据导向
  特征：提问精准、关注数据和细节、喜欢对比分析、决策谨慎

【任务】
请分析该用户的 DISC 类型，并以 JSON 格式返回：
{{
    "disc_type": "D/I/S/C",
    "secondary_type": "次要类型（可选）",
    "confidence": 0.95,
    "evidence": [
        {{"quote": "用户原话片段", "reason": "这句话体现了什么特征"}},
        ...
    ],
    "interaction_style": "针对该类型的沟通建议",
    "decision_factors": ["影响该用户决策的关键因素"],
    "risk_aversion": "high/medium/low"
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "你是专业的用户心理分析师，输出严格的 JSON 格式。"
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        import json
        result = json.loads(response.choices[0].message.content or "{}")

        return {
            "user_id": user_id,
            "disc_type": result.get("disc_type", "unknown"),
            "secondary_type": result.get("secondary_type"),
            "confidence": result.get("confidence", 0.0),
            "evidence": result.get("evidence", []),
            "interaction_style": result.get("interaction_style", ""),
            "decision_factors": result.get("decision_factors", []),
            "risk_aversion": result.get("risk_aversion", "medium"),
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def batch_analyze(
        self,
        users_conversations: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        批量分析多个用户

        Args:
            users_conversations: {user_id: conversations} 字典

        Returns:
            DISC 报告列表
        """
        return [
            self.analyze_user(convs, user_id)
            for user_id, convs in users_conversations.items()
        ]

    def _compress_conversations(
        self,
        conversation_history: List[Dict[str, Any]],
        max_turns: int = 20,
        max_length: int = 3000
    ) -> str:
        """
        压缩长文本对话：智能选择最具代表性的对话片段

        Args:
            conversation_history: 完整对话历史
            max_turns: 最多保留多少轮对话
            max_length: 最大字符数

        Returns:
            压缩后的对话文本
        """
        if not conversation_history:
            return "暂无对话记录"

        # 如果对话较少，直接返回
        if len(conversation_history) <= max_turns:
            formatted = self._format_conversations(conversation_history)
            if len(formatted) <= max_length:
                return formatted

        # 智能采样：选择不同阶段的代表性对话
        sampled = self._intelligent_sample(conversation_history, max_turns)
        formatted = self._format_conversations(sampled)

        # 如果仍然超长，进行截断
        if len(formatted) > max_length:
            formatted = formatted[:max_length] + "\n... (后续内容已省略)"

        return formatted

    def _intelligent_sample(
        self,
        conversations: List[Dict[str, Any]],
        sample_size: int
    ) -> List[Dict[str, Any]]:
        """
        智能采样：确保覆盖对话的不同阶段（早期、中期、近期）
        """
        n = len(conversations)
        if n <= sample_size:
            return conversations

        sampled = []

        # 早期对话（前 30%）
        early_count = int(sample_size * 0.3)
        sampled.extend(conversations[:early_count])

        # 中期对话（中间 40%）
        middle_start = int(n * 0.3)
        middle_end = int(n * 0.7)
        middle_conversations = conversations[middle_start:middle_end]
        middle_count = int(sample_size * 0.4)
        if middle_conversations:
            step = len(middle_conversations) // middle_count
            sampled.extend(middle_conversations[::step][:middle_count])

        # 近期对话（后 30%）
        recent_count = int(sample_size * 0.3)
        sampled.extend(conversations[-recent_count:])

        return sampled

    @staticmethod
    def _format_conversations(conversation_history: List[Dict[str, Any]]) -> str:
        """将对话历史格式化为易读文本"""
        formatted = []
        for i, conv in enumerate(conversation_history, 1):
            user_input = conv.get("user_input", "")
            assistant_response = conv.get("assistant_response", "")
            timestamp = conv.get("timestamp", "")

            formatted.append(
                f"【对话 {i}】({timestamp})\n"
                f"客户: {user_input}\n"
                f"顾问: {assistant_response}\n"
            )

        return "\n".join(formatted)


from datetime import datetime
