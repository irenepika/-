"""
Judge Evaluator - LLM-as-a-Judge 评测裁判
负责高维度的离线打分（转化潜力、话术专业度、合规性等）
"""
from typing import Dict, Any
from openai import OpenAI


class JudgeEvaluator:
    """
    测评裁判：使用 LLM-as-a-Judge 模式对历史日志进行多维度打分
    支持离线批量评估，生成 Benchmark 报告
    """

    def __init__(self, model: str = "gpt-4o"):
        self.client = OpenAI()
        self.model = model

    def evaluate_conversation(
        self,
        conversation: Dict[str, Any],
        evaluation_criteria: list[str]
    ) -> Dict[str, Any]:
        """
        对单个对话进行多维度评测

        Args:
            conversation: 完整对话记录（包含用户输入、系统回复、上下文等）
            evaluation_criteria: 评测维度列表，如：
                - conversion_potential: 转化潜力（话术是否有效引导客户）
                - professionalism: 专业度（产品知识是否准确）
                - compliance: 合规性（是否有误导性表述）
                - empathy: 同理心（是否理解客户需求）
                - clarity: 表达清晰度

        Returns:
            包含各维度分数和详细反馈的评测结果
        """
        conversation_text = self._format_conversation(conversation)

        criteria_descriptions = {
            "conversion_potential": "转化潜力：话术是否有效引导客户向购买决策推进",
            "professionalism": "专业度：保险知识是否准确，是否能解答客户疑问",
            "compliance": "合规性：是否有夸大收益、隐瞒风险等违规表述",
            "empathy": "同理心：是否理解客户真实需求，是否建立信任",
            "clarity": "表达清晰度：语言是否简洁明了，逻辑是否清晰"
        }

        criteria_prompt = "\n".join([
            f"{i+1}. {criteria_descriptions.get(c, c)}"
            for i, c in enumerate(evaluation_criteria)
        ])

        prompt = f"""你是一位资深的保险销售培训专家。请对以下对话进行专业评测。

【对话记录】
{conversation_text}

【评测维度】
{criteria_prompt}

【评分标准】
- 每个维度满分 10 分
- 9-10 分：卓越，表现极佳
- 7-8 分：优秀，有改进空间
- 5-6 分：合格，需重点提升
- 1-4 分：不合格，存在明显问题

请以 JSON 格式返回评测结果：
{{
    "overall_score": 8.5,
    "dimension_scores": {{
        "conversion_potential": {{"score": 8, "feedback": "具体反馈..."}},
        "professionalism": {{"score": 9, "feedback": "具体反馈..."}},
        ...
    }},
    "strengths": ["优点1", "优点2"],
    "improvement_areas": ["改进点1", "改进点2"],
    "summary": "总体评价"
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是保险销售评测专家，输出严格的 JSON 格式。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        import json
        result = json.loads(response.choices[0].message.content or "{}")

        return {
            "conversation_id": conversation.get("id", "unknown"),
            "overall_score": result.get("overall_score", 0),
            "dimension_scores": result.get("dimension_scores", {}),
            "strengths": result.get("strengths", []),
            "improvement_areas": result.get("improvement_areas", []),
            "summary": result.get("summary", "")
        }

    def batch_evaluate(
        self,
        conversations: list[Dict[str, Any]],
        evaluation_criteria: list[str]
    ) -> Dict[str, Any]:
        """
        批量评测多个对话，生成汇总报告

        Args:
            conversations: 对话列表
            evaluation_criteria: 评测维度列表

        Returns:
            汇总统计和 Benchmark 报告
        """
        results = [self.evaluate_conversation(conv, evaluation_criteria) for conv in conversations]

        # 计算汇总统计
        overall_scores = [r["overall_score"] for r in results]
        avg_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0

        # 维度平均分
        dimension_avgs = {}
        for crit in evaluation_criteria:
            scores = [
                r["dimension_scores"].get(crit, {}).get("score", 0)
                for r in results
            ]
            dimension_avgs[crit] = sum(scores) / len(scores) if scores else 0

        return {
            "total_conversations": len(conversations),
            "average_overall_score": avg_score,
            "dimension_averages": dimension_avgs,
            "top_performers": sorted(results, key=lambda x: x["overall_score"], reverse=True)[:3],
            "bottom_performers": sorted(results, key=lambda x: x["overall_score"])[:3],
            "individual_results": results
        }

    def _format_conversation(self, conversation: Dict[str, Any]) -> str:
        """格式化对话记录为易读文本"""
        turns = conversation.get("turns", [])
        formatted = []

        for turn in turns:
            role = turn.get("role", "unknown")
            content = turn.get("content", "")
            role_name = {"user": "客户", "assistant": "顾问"}.get(role, role)
            formatted.append(f"{role_name}: {content}")

        # 添加元数据
        metadata = conversation.get("metadata", {})
        if metadata:
            formatted.insert(0, f"【元数据】客户ID: {metadata.get('user_id', 'N/A')}, "
                             f"DISC类型: {metadata.get('disc_type', 'N/A')}, "
                             f"最终结果: {metadata.get('outcome', 'N/A')}")

        return "\n\n".join(formatted)
