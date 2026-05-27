"""
Run Batch Evaluations
一键跑通所有评估任务，输出 Benchmark 报告
"""
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from templates.model_graded import ModelGradedEvaluator
from templates.exact_match import ExactMatchEvaluator


class EvalRunner:
    """
    评估运行器：加载评测配置，执行评估任务，生成报告
    """

    def __init__(self, config_path: str = "evals/registry/insurance_evals.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.output_dir = Path(self.config["reporting"]["output_dir"])
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化评估器
        self.model_evaluator = ModelGradedEvaluator()
        self.exact_evaluator = ExactMatchEvaluator()

    def run_all_tasks(self) -> Dict[str, Any]:
        """运行所有评测任务"""
        all_results = {}

        for task in self.config["evaluation_tasks"]:
            task_name = task["name"]
            print(f"\n{'='*60}")
            print(f"Running Task: {task_name}")
            print(f"Description: {task['description']}")
            print(f"{'='*60}")

            result = self._run_single_task(task)
            all_results[task_name] = result

            # 打印简要结果
            self._print_task_summary(task_name, result)

        # 生成汇总报告
        summary = self._generate_summary(all_results)

        # 保存报告
        self._save_reports(all_results, summary)

        return summary

    def _run_single_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """运行单个评测任务"""
        dataset_path = Path(task["dataset"])
        template = task["template"]
        metrics = task["metrics"]
        threshold = task["pass_threshold"]

        # 加载测试数据
        test_cases = self._load_dataset(dataset_path)

        # 选择评估器
        if "model_graded" in template:
            criteria = {
                "metrics": metrics,
                "pass_threshold": threshold
            }
            results = self.model_evaluator.batch_evaluate(test_cases, criteria)
        elif "exact_match" in template:
            criteria = {
                "pass_threshold": threshold
            }
            results = self.exact_evaluator.batch_evaluate(test_cases, criteria)
        else:
            raise ValueError(f"Unknown template: {template}")

        return results

    def _load_config(self) -> Dict[str, Any]:
        """加载评测配置"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _load_dataset(self, dataset_path: Path) -> List[Dict[str, Any]]:
        """加载测试数据集（JSONL 格式）"""
        test_cases = []

        with open(dataset_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    test_cases.append(json.loads(line))

        return test_cases

    def _print_task_summary(self, task_name: str, result: Dict[str, Any]):
        """打印任务简要结果"""
        print(f"\n【{task_name}】结果:")
        print(f"  总用例数: {result.get('total_cases', 0)}")

        if "average_score" in result:
            print(f"  平均分: {result['average_score']:.2f}")
        else:
            print(f"  通过数: {result.get('passed_count', 0)}")
            print(f"  通过率: {result.get('pass_rate', 0)*100:.1f}%")

        passed = result.get("passed", False)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  状态: {status}")

    def _generate_summary(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成汇总报告"""
        total_tasks = len(all_results)
        passed_tasks = sum(1 for r in all_results.values() if r.get("passed", False))

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_tasks": total_tasks,
            "passed_tasks": passed_tasks,
            "overall_pass_rate": passed_tasks / total_tasks if total_tasks > 0 else 0,
            "task_results": {
                name: {
                    "passed": result.get("passed", False),
                    "score": result.get("average_score", result.get("pass_rate", 0))
                }
                for name, result in all_results.items()
            }
        }

    def _save_reports(
        self,
        all_results: Dict[str, Any],
        summary: Dict[str, Any]
    ):
        """保存评测报告（JSON、Markdown、HTML）"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base_name = f"benchmark_report_{timestamp}"

        # JSON 报告
        json_path = self.output_dir / f"{base_name}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": summary,
                "detailed_results": all_results
            }, f, ensure_ascii=False, indent=2)
        print(f"\n📊 JSON 报告已保存: {json_path}")

        # Markdown 报告
        md_path = self.output_dir / f"{base_name}.md"
        md_content = self._generate_markdown_report(summary, all_results)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"📄 Markdown 报告已保存: {md_path}")

        # HTML 报告
        html_path = self.output_dir / f"{base_name}.html"
        html_content = self._generate_html_report(summary, all_results)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"🌐 HTML 报告已保存: {html_path}")

    def _generate_markdown_report(
        self,
        summary: Dict[str, Any],
        all_results: Dict[str, Any]
    ) -> str:
        """生成 Markdown 格式报告"""
        lines = [
            "# 保险 Agent 评测报告",
            f"\n**生成时间**: {summary['timestamp']}",
            f"**总任务数**: {summary['total_tasks']}",
            f"**通过任务数**: {summary['passed_tasks']}",
            f"**总体通过率**: {summary['overall_pass_rate']*100:.1f}%",
            "\n## 任务详情\n"
        ]

        for task_name, result in all_results.items():
            status = "✅ 通过" if result.get("passed") else "❌ 失败"
            lines.append(f"### {task_name} - {status}")

            if "average_score" in result:
                lines.append(f"- 平均分: {result['average_score']:.2f}")
            else:
                lines.append(f"- 通过率: {result['pass_rate']*100:.1f}%")

            lines.append(f"- 总用例: {result['total_cases']}\n")

        return "\n".join(lines)

    def _generate_html_report(
        self,
        summary: Dict[str, Any],
        all_results: Dict[str, Any]
    ) -> str:
        """生成 HTML 格式报告"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>保险 Agent 评测报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 20px; border-radius: 8px; }}
        .task {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .pass {{ border-left: 4px solid #4caf50; }}
        .fail {{ border-left: 4px solid #f44336; }}
        .metric {{ display: inline-block; margin: 5px 10px 5px 0; }}
    </style>
</head>
<body>
    <h1>📊 保险 Agent 评测报告</h1>
    <div class="summary">
        <p><strong>生成时间:</strong> {summary['timestamp']}</p>
        <p><strong>总任务数:</strong> {summary['total_tasks']}</p>
        <p><strong>通过任务数:</strong> {summary['passed_tasks']}</p>
        <p><strong>总体通过率:</strong> {summary['overall_pass_rate']*100:.1f}%</p>
    </div>

    <h2>任务详情</h2>
"""

        for task_name, result in all_results.items():
            css_class = "pass" if result.get("passed") else "fail"
            status = "✅ 通过" if result.get("passed") else "❌ 失败"

            html += f"""
    <div class="task {css_class}">
        <h3>{task_name} - {status}</h3>
        <div class="metrics">
"""

            if "average_score" in result:
                html += f"            <span class='metric'>平均分: {result['average_score']:.2f}</span>\n"
            else:
                html += f"            <span class='metric'>通过率: {result['pass_rate']*100:.1f}%</span>\n"

            html += f"            <span class='metric'>总用例: {result['total_cases']}</span>\n"
            html += "        </div>\n    </div>\n"

        html += """
</body>
</html>
"""
        return html


def main():
    """主入口：运行所有评测任务"""
    runner = EvalRunner()
    summary = runner.run_all_tasks()

    print("\n" + "="*60)
    print("🎉 所有评测任务完成！")
    print(f"总体通过率: {summary['overall_pass_rate']*100:.1f}%")
    print("="*60)


if __name__ == "__main__":
    main()
