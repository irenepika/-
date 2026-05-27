"""
Guardrails - 在线防护墙
轻量级合规 Regex/极速 API 拦截（0 延迟）
"""
import re
from typing import Dict, Any, List


class Guardrails:
    """
    在线合规拦截器：实时检测用户输入和系统回复的合规性
    使用规则引擎实现零延迟的即时拦截
    """

    def __init__(self):
        # 敏感词列表（可根据实际需求扩展）
        self.sensitive_keywords = [
            "诈骗", "传销", "洗钱", "非法集资",
            "高收益", "保本保息", "零风险", "稳赚不赔",
            "内幕消息", "内部渠道", "特殊关系"
        ]

        # 编译正则表达式以提高性能
        self.keyword_patterns = [
            re.compile(keyword) for keyword in self.sensitive_keywords
        ]

        # PII 检测模式（银行卡、身份证等）
        self.pi i_patterns = {
            "bank_card": re.compile(r'\b\d{16,19}\b'),
            "id_card": re.compile(r'\b\d{17}[\dXx]\b'),
            "phone": re.compile(r'\b1[3-9]\d{9}\b'),
        }

    def check_input(self, user_input: str) -> Dict[str, Any]:
        """
        检查用户输入的合规性

        Args:
            user_input: 用户输入文本

        Returns:
            {
                "allowed": bool,  # 是否允许通过
                "reason": str,    # 如果不通过，说明原因
                "block_message": str  # 返回给用户的提示
            }
        """
        # 检查敏感词
        for pattern in self.keyword_patterns:
            if pattern.search(user_input):
                return {
                    "allowed": False,
                    "reason": "sensitive_keyword_detected",
                    "block_message": "抱歉，您的输入包含敏感词汇，请重新表述。"
                }

        # 检查是否包含 PII（可选：某些场景下需要保护用户隐私）
        detected_pii = []
        for pii_type, pattern in self.pii_patterns.items():
            if pattern.search(user_input):
                detected_pii.append(pii_type)

        if detected_pii:
            # 可以选择警告或拦截
            return {
                "allowed": True,  # 允许通过但记录
                "reason": f"pii_detected: {', '.join(detected_pii)}",
                "block_message": "",
                "warning": f"检测到敏感信息：{', '.join(detected_pii)}"
            }

        return {
            "allowed": True,
            "reason": "passed",
            "block_message": ""
        }

    def check_output(self, agent_output: str) -> Dict[str, Any]:
        """
        检查 Agent 输出的合规性（防止 Agent 生成不当内容）

        Args:
            agent_output: Agent 生成的回复

        Returns:
            合规检查结果
        """
        # 检查是否包含夸大收益的表述
        exaggerated_claims = [
            "保证", "必定", "100%", "绝无风险",
            "稳赚", "必定赚钱", "无风险高收益"
        ]

        for claim in exaggerated_claims:
            if claim in agent_output:
                return {
                    "allowed": False,
                    "reason": "exaggerated_claim_detected",
                    "block_message": "【系统拦截】回复包含夸大表述，已自动过滤"
                }

        # 检查是否包含必要的风险提示
        if any(word in agent_output for word in ["收益", "回报", "分红"]):
            if "风险" not in agent_output and "提示" not in agent_output:
                return {
                    "allowed": False,
                    "reason": "missing_risk_warning",
                    "block_message": "【系统拦截】涉及收益表述必须包含风险提示"
                }

        return {
            "allowed": True,
            "reason": "passed",
            "block_message": ""
        }

    def sanitize_input(self, user_input: str) -> str:
        """
        清理用户输入：移除 PII 等敏感信息

        Args:
            user_input: 原始用户输入

        Returns:
            清理后的文本
        """
        sanitized = user_input

        # 替换银行卡号
        sanitized = self.pii_patterns["bank_card"].sub('****', sanitized)

        # 替换身份证号
        sanitized = self.pii_patterns["id_card"].sub('****', sanitized)

        # 替换手机号
        sanitized = self.pii_patterns["phone"].sub('***', sanitized)

        return sanitized
