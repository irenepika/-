"""
Sales Actor - 销售主干 Agent
专注话术生成与转化，不负责状态判定
"""
from typing import Optional, Dict, Any
from openai import OpenAI
from schemas.state_models import UserProfile, FunnelState


class SalesActor:
    """销售话术生成器，负责将用户输入转化为符合保险销售规范的话术"""

    def __init__(self, model: str = "gpt-4o"):
        self.client = OpenAI()
        self.model = model

    def generate_response(
        self,
        user_input: str,
        user_profile: UserProfile,
        conversation_history: list[Dict[str, str]],
        available_tools: list[Dict[str, Any]]
    ) -> str:
        """
        生成销售回复话术

        Args:
            user_input: 用户当前输入
            user_profile: 用户画像（包含 DISC 性格标签）
            conversation_history: 对话历史上下文
            available_tools: 可用的工具列表（如计算器、条款检索等）

        Returns:
            生成的销售话术
        """
        system_prompt = self._build_system_prompt(user_profile)
        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_history,
            {"role": "user", "content": user_input}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=available_tools,
            temperature=0.8  # 销售场景需要一定的灵活性
        )

        return response.choices[0].message.content or ""

    def _build_system_prompt(self, user_profile: UserProfile) -> str:
        """根据用户 DISC 画像构建个性化的系统提示词"""
        disc_hints = {
            "D": "直接、果断，强调结果和效率，避免啰嗦",
            "I": "热情、互动性强，多讲故事和案例，建立情感连接",
            "S": "温和、稳健，强调安全保障和服务承诺，避免高压销售",
            "C": "理性、数据驱动，提供详细分析和条款对比，尊重其决策节奏"
        }

        hint = disc_hints.get(user_profile.disc_type, "专业、友善")

        return f"""你是一名专业的保险销售顾问，正在与客户沟通。

【客户画像】
- DISC 类型：{user_profile.disc_type}
- 沟通风格建议：{hint}
- 历史互动阶段：{user_profile.interaction_stage}

【核心原则】
1. 以客户需求为中心，不是推销产品而是解决问题
2. 保持专业和真诚，避免夸大收益或隐瞒风险
3. 根据 DISC 类型调整沟通节奏和话术风格
4. 在适当时候引导客户进入下一步（如需求调研、方案介绍、促成签约）

当前阶段目标：基于客户画像和对话历史，生成最合适的回复话术。"""
