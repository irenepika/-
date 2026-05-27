"""
Calculator - 保费测算与条款检索 Mock 工具
演示 Agent 如何使用外部工具增强能力
"""
from typing import Dict, Any


class InsuranceCalculator:
    """保险计算器：保费测算、收益演示等"""

    @staticmethod
    def calculate_premium(
        coverage_amount: int,
        age: int,
        gender: str,
        payment_period: int
    ) -> Dict[str, Any]:
        """
        计算保费（Mock 实现）

        Args:
            coverage_amount: 保额（元）
            age: 被保人年龄
            gender: 性别（male/female）
            payment_period: 缴费期（年）

        Returns:
            保费计算结果
        """
        # 简化的费率计算逻辑（实际应使用保险精算表）
        base_rate = 0.001  # 基础费率
        age_factor = 1 + (age - 30) * 0.02  # 年龄系数
        gender_factor = 0.9 if gender == "female" else 1.0  # 性别系数
        period_factor = 1 + (10 - payment_period) * 0.05  # 缴费期系数

        annual_premium = coverage_amount * base_rate * age_factor * gender_factor * period_factor

        return {
            "coverage_amount": coverage_amount,
            "annual_premium": round(annual_premium, 2),
            "payment_period": payment_period,
            "total_premium": round(annual_premium * payment_period, 2),
            "currency": "CNY"
        }

    @staticmethod
    def estimate_returns(
        premium: int,
        years: int,
        expected_rate: float = 0.035
    ) -> Dict[str, Any]:
        """
        估算保险收益（Mock 实现）

        Args:
            premium: 年缴保费
            years: 保险期间
            expected_rate: 预期收益率

        Returns:
            收益估算结果
        """
        # 简化的复利计算
        total_premium = premium * years
        final_value = sum(
            premium * (1 + expected_rate) ** (years - i)
            for i in range(years)
        )

        return {
            "total_premium": total_premium,
            "expected_final_value": round(final_value, 2),
            "expected_gain": round(final_value - total_premium, 2),
            "expected_rate": expected_rate,
            "disclaimer": "收益演示仅供参考，实际收益以合同约定为准"
        }


class ClauseRetriever:
    """条款检索器：查询保险产品条款"""

    @staticmethod
    def search_clause(keyword: str, product_type: str = "life") -> Dict[str, Any]:
        """
        搜索保险条款（Mock 实现）

        Args:
            keyword: 搜索关键词
            product_type: 产品类型（life/health/accident）

        Returns:
            匹配的条款内容
        """
        # Mock 条款数据库
        mock_clauses = {
            "life": {
                "等待期": "本产品等待期为 90 天，等待期内因疾病导致的不承担保险责任。",
                "豁免": "投保人遭受意外伤害身故或全残，可豁免后续保费。",
                "身故": "被保人身故，按基本保额给付身故保险金。"
            },
            "health": {
                "等待期": "本产品等待期为 180 天。",
                "免赔额": "年度免赔额 1 万元，社保报销后可抵扣。",
                "赔付比例": "社保报销后 100%，未经社保报销 60%。"
            }
        }

        clauses = mock_clauses.get(product_type, {})

        # 简单的关键词匹配
        matched = []
        for key, value in clauses.items():
            if keyword in key or keyword in value:
                matched.append({"条款": key, "内容": value})

        return {
            "keyword": keyword,
            "product_type": product_type,
            "matched_clauses": matched if matched else [{"提示": "未找到匹配条款，请提供更具体的关键词"}]
        }


def register_default_tools(registry):
    """
    将默认工具注册到 ToolRegistry

    Args:
        registry: ToolRegistry 实例
    """
    calc = InsuranceCalculator()
    retriever = ClauseRetriever()

    # 注册保费计算工具
    registry.register_tool(
        name="calculate_premium",
        description="计算保险保费，根据保额、年龄、性别和缴费期计算年缴保费",
        func=calc.calculate_premium,
        parameters={
            "type": "object",
            "properties": {
                "coverage_amount": {
                    "type": "integer",
                    "description": "保额（元）"
                },
                "age": {
                    "type": "integer",
                    "description": "被保人年龄"
                },
                "gender": {
                    "type": "string",
                    "enum": ["male", "female"],
                    "description": "性别"
                },
                "payment_period": {
                    "type": "integer",
                    "description": "缴费期（年）"
                }
            },
            "required": ["coverage_amount", "age", "gender", "payment_period"]
        }
    )

    # 注册收益估算工具
    registry.register_tool(
        name="estimate_returns",
        description="估算保险收益，演示保单未来的现金价值",
        func=calc.estimate_returns,
        parameters={
            "type": "object",
            "properties": {
                "premium": {
                    "type": "integer",
                    "description": "年缴保费（元）"
                },
                "years": {
                    "type": "integer",
                    "description": "保险期间（年）"
                },
                "expected_rate": {
                    "type": "number",
                    "description": "预期收益率（可选）"
                }
            },
            "required": ["premium", "years"]
        }
    )

    # 注册条款检索工具
    registry.register_tool(
        name="search_clause",
        description="检索保险条款，查询产品具体保障内容",
        func=retriever.search_clause,
        parameters={
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词，如'等待期'、'豁免'等"
                },
                "product_type": {
                    "type": "string",
                    "enum": ["life", "health", "accident"],
                    "description": "产品类型"
                }
            },
            "required": ["keyword"]
        }
    )
