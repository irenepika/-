"""
Exact Match Evaluation Template
规则匹配评估模板：基于关键词、正则等规则进行精确匹配
"""
import re
from typing import Dict, Any, List


class ExactMatchEvaluator:
    """
    精确匹配评估器
    基于规则（关键词、正则表达式等）进行快速的合规性检查
    """

    def evaluate(
        self,
        input_text: str,
        actual_output: str,
        expected_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        基于规则评估输出

        Args:
            input_text: 用户输入
            actual_output: Agent 实际输出
            expected_criteria: 评测标准，包含：
                - expected_keywords: 必须包含的关键词
                - forbidden_keywords: 禁止出现的关键词
                - regex_pattern: 正则表达式匹配

        Returns:
            评估结果
        """
        result = {
            "input": input_text,
            "output": actual_output,
            "passed": True,
            "details": {}
        }

        # 检查必须包含的关键词
        expected_keywords = expected_criteria.get("expected_keywords", [])
        if expected_keywords:
            keyword_check = self._check_keywords(actual_output, expected_keywords)
            result["details"]["expected_keywords"] = keyword_check
            if not keyword_check["all_present"]:
                result["passed"] = False

        # 检查禁止的关键词
        forbidden_keywords = expected_criteria.get("forbidden_keywords", [])
        if forbidden_keywords:
            forbidden_check = self._check_forbidden(actual_output, forbidden_keywords)
            result["details"]["forbidden_keywords"] = forbidden_check
            if forbidden_check["found_forbidden"]:
                result["passed"] = False

        # 检查正则表达式
        regex_pattern = expected_criteria.get("regex_pattern")
        if regex_pattern:
            regex_check = self._check_regex(actual_output, regex_pattern)
            result["details"]["regex_match"] = regex_check
            if not regex_check["matched"]:
                result["passed"] = False

        result["reason"] = self._generate_reason(result["details"])

        return result

    def _check_keywords(
        self,
        text: str,
        keywords: List[str]
    ) -> Dict[str, Any]:
        """检查必须包含的关键词"""
        found = [kw for kw in keywords if kw in text]
        missing = [kw for kw in keywords if kw not in text]

        return {
            "all_present": len(missing) == 0,
            "found": found,
            "missing": missing
        }

    def _check_forbidden(
        self,
        text: str,
        forbidden_keywords: List[str]
    ) -> Dict[str, Any]:
        """检查禁止出现的关键词"""
        found = [kw for kw in forbidden_keywords if kw in text]

        return {
            "found_forbidden": len(found) > 0,
            "forbidden_found": found
        }

    def _check_regex(self, text: str, pattern: str) -> Dict[str, Any]:
        """检查正则表达式"""
        match = re.search(pattern, text)

        return {
            "matched": match is not None,
            "matched_text": match.group() if match else None
        }

    def _generate_reason(self, details: Dict[str, Any]) -> str:
        """生成未通过的原因说明"""
        reasons = []

        if "expected_keywords" in details:
            kw_detail = details["expected_keywords"]
            if not kw_detail["all_present"]:
                reasons.append(f"缺少关键词: {', '.join(kw_detail['missing'])}")

        if "forbidden_keywords" in details:
            fb_detail = details["forbidden_keywords"]
            if fb_detail["found_forbidden"]:
                reasons.append(f"包含禁止词: {', '.join(fb_detail['forbidden_found'])}")

        if "regex_match" in details:
            rx_detail = details["regex_match"]
            if not rx_detail["matched"]:
                reasons.append("未匹配正则表达式")

        return "; ".join(reasons) if reasons else "通过所有检查"

    def batch_evaluate(
        self,
        test_cases: List[Dict[str, Any]],
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
                expected_criteria={
                    **criteria,
                    **case  # 用例级别的标准可以覆盖全局标准
                }
            )
            results.append(result)
            if result["passed"]:
                passed_count += 1

        # 统计
        pass_rate = passed_count / len(results) if results else 0

        return {
            "total_cases": len(results),
            "passed_count": passed_count,
            "pass_rate": pass_rate,
            "passed": pass_rate >= criteria.get("pass_threshold", 0.9),
            "individual_results": results
        }
