"""
Model Graded Evaluation Template
LLM-as-a-Judge 评估模板：使用大模型对回复进行多维度打分
"""
from typing import Dict, Any
from openai import OpenAI


class ModelGradedEvaluator:
    """
    LLM-as-a-Judge 评估器
    使用 GPT-4o 等大模型作为裁判，对 Agent 回复进行多维度评分
    """

    def __init__(self, judge_model: str = "gpt-4o"):
        self.client = OpenAI()
        self.judge_model = judge_model

    def evaluate(
        self,
        input_text: str,
        actual_output: str,
        expected_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        使用 LLM 对输出进行评分

        Args:
            input_text: 用户输入
            actual_output: Agent 实际输出
            expected_criteria: 评测标准（从 YAML/JSONL 中读取）

        Returns:
            评分结果
        """
        metrics = expected_criteria.get("metrics", [])
        category = expected_criteria.get("category", "general")

        prompt = self._build_judge_prompt(
            input_text, actual_output, metrics, category
        )

        response = self.client.chat.completions.create(
            model=self.judge_model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一位专业的保险销售质检专家。输出严格的 JSON 格式评分。"
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        import json
        result = json.loads(response.choices[0].message.content or "{}")

        return {
            "input": input_text,
            "output": actual_output,
            "scores": result.get("scores", {}),
            "overall_score": result.get("overall_score", 0),
            "feedback": result.get("feedback", ""),
            "passed": result.get("overall_score", 0) >= expected_criteria.get("pass_threshold", 7.0)
        }

    def _build_judge_prompt(
        self,
        input_text: str,
        actual_output: str,
        metrics: list[str],
        category: str
    ) -> str:
        """构建 Judge 提示词"""

        metric_descriptions = {
            "conversion_potential": "转化潜力：话术是否有效引导客户向购买决策推进",
            "professionalism": "专业度：保险知识是否准确，是否能解答客户疑问",
            "empathy": "同理心：是否理解客户真实需求，是否建立信任",
            "clarity": "表达清晰度：语言是否简洁明了，逻辑是否清晰",
            "style_match_score": "风格适配：话术风格是否符合客户画像（DISC）",
            "appropriate_tone": "语气恰当性：语气是否专业、友善、不卑不亢"
        }

        metrics_prompt = "\n".join([
            f"- {m}: {metric_descriptions.get(m, m)}"
            for m in metrics
        ])

        return f"""请对以下保险销售对话进行评分。

【用户输入】
{input_text}

【Agent 回复】
{actual_output}

【评测维度】
{metrics_prompt}

【评分标准】
每个维度满分 10 分：
- 9-10 分：卓越，表现极佳
- 7-8 分：优秀，有改进空间
- 5-6 分：合格，需重点提升
- 1-4 分：不合格，存在明显问题

【输出格式】
请以 JSON 格式返回：
{{
    "overall_score": 8.5,
    "scores": {{
        "conversion_potential": 8,
        "professionalism": 9,
        ...
    }},
    "feedback": "简要评价，指出优点和改进点"
}}"""

    def batch_evaluate(
        self,
        test_cases: list[Dict[str, Any]],
        criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        批量评估

        Args:
            test_cases: 测试用例列表
            criteria: 评测标准

        Returns:
            汇总报告
        """
        results = []
        passed_count = 0

        for case in test_cases:
            result = self.evaluate(
                input_text=case["input"],
                actual_output=case.get("actual_output", ""),
                expected_criteria=criteria
            )
            results.append(result)
            if result["passed"]:
                passed_count += 1

        # 计算汇总统计
        overall_scores = [r["overall_score"] for r in results]
        pass_rate = passed_count / len(results) if results else 0

        return {
            "total_cases": len(results),
            "passed_count": passed_count,
            "pass_rate": pass_rate,
            "average_score": sum(overall_scores) / len(overall_scores) if overall_scores else 0,
            "individual_results": results
        }
