"""
Evaluation Metrics - 评测结果数据模型
定义评测过程中的各类指标和结果结构
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class DimensionScore(BaseModel):
    """单个维度的评分结果"""
    dimension_name: str = Field(..., description="维度名称")
    score: float = Field(..., ge=0.0, le=10.0, description="分数（0-10）")
    feedback: str = Field(..., description="详细反馈")
    passed: bool = Field(..., description="是否通过阈值")


class EvaluationResult(BaseModel):
    """单个评测任务的完整结果"""
    task_name: str = Field(..., description="任务名称")
    evaluator_type: Literal["model_graded", "exact_match"] = Field(
        ...,
        description="评估器类型"
    )

    # 评测对象
    input_text: str = Field(..., description="输入文本")
    output_text: str = Field(..., description="输出文本")

    # 评分结果
    overall_score: Optional[float] = Field(None, description="总体分数（如有）")
    passed: bool = Field(..., description="是否通过")
    dimension_scores: Dict[str, DimensionScore] = Field(
        default_factory=dict,
        description="各维度分数"
    )

    # 详细反馈
    feedback: str = Field(default="", description="总体反馈")
    strengths: list[str] = Field(default_factory=list, description="优点")
    improvement_areas: list[str] = Field(default_factory=list, description="改进点")

    # 元数据
    evaluated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="评测时间"
    )
    model_version: Optional[str] = Field(None, description="使用的模型版本")


class BatchEvaluationSummary(BaseModel):
    """批量评测的汇总报告"""
    batch_id: str = Field(..., description="批次 ID")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="评测时间"
    )

    # 总体统计
    total_tasks: int = Field(..., description="总任务数")
    passed_tasks: int = Field(..., description="通过任务数")
    overall_pass_rate: float = Field(..., description="总体通过率")

    # 任务级结果
    task_results: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="各任务的评测结果"
    )

    # 趋势分析（可选）
    previous_batch_comparison: Optional[Dict[str, float]] = Field(
        None,
        description="与上一批次的对比"
    )


class ComplianceTestResult(BaseModel):
    """合规性测试结果（Exact Match 类）"""
    test_id: str = Field(..., description="测试用例 ID")
    category: str = Field(..., description="测试类别")
    input: str = Field(..., description="用户输入")
    output: str = Field(..., description="Agent 输出")

    # 关键词检查
    expected_keywords_found: list[str] = Field(
        ...,
        description="找到的必须包含的关键词"
    )
    expected_keywords_missing: list[str] = Field(
        ...,
        description="缺失的必须包含的关键词"
    )
    forbidden_keywords_found: list[str] = Field(
        ...,
        description="找到的禁止关键词"
    )

    # 判定
    passed: bool = Field(..., description="是否通过")
    reason: str = Field(..., description="未通过的原因")


class ModelGradedTestResult(BaseModel):
    """模型评分测试结果（Model Graded 类）"""
    test_id: str = Field(..., description="测试用例 ID")
    category: str = Field(..., description="测试类别")

    # 输入输出
    input: str = Field(..., description="用户输入")
    output: str = Field(..., description="Agent 输出")

    # 评分
    overall_score: float = Field(..., ge=0.0, le=10.0, description="总体分数")
    dimension_scores: Dict[str, float] = Field(..., description="各维度分数")

    # 反馈
    feedback: str = Field(..., description="详细反馈")
    strengths: list[str] = Field(default_factory=list, description="优点")
    improvement_areas: list[str] = Field(default_factory=list, description="改进点")

    # 判定
    passed: bool = Field(..., description="是否通过阈值")
    threshold: float = Field(..., description="通过的阈值分数")


class BenchmarkReport(BaseModel):
    """完整的 Benchmark 报告"""
    report_id: str = Field(..., description="报告 ID")
    generated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="生成时间"
    )

    # 汇总信息
    summary: BatchEvaluationSummary = Field(..., description="汇总统计")

    # 详细结果
    compliance_results: list[ComplianceTestResult] = Field(
        default_factory=list,
        description="合规性测试详细结果"
    )
    model_graded_results: list[ModelGradedTestResult] = Field(
        default_factory=list,
        description="模型评分测试详细结果"
    )

    # 元数据
    model_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="模型配置信息"
    )
    evaluator_version: str = Field(default="1.0.0", description="评估器版本")


class PerformanceMetrics(BaseModel):
    """性能指标：用于监控系统的运行效率"""
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="记录时间"
    )

    # 延迟指标
    avg_response_time_ms: float = Field(..., description="平均响应时间（毫秒）")
    p95_response_time_ms: float = Field(..., description="P95 响应时间")
    p99_response_time_ms: float = Field(..., description="P99 响应时间")

    # 吞吐量
    requests_per_second: float = Field(..., description="每秒请求数")

    # 错误率
    error_rate: float = Field(..., description="错误率")

    # 组件级指标
    actor_latency_ms: float = Field(..., description="Sales Actor 延迟")
    classifier_latency_ms: float = Field(..., description="Intent Classifier 延迟")
    guardrails_latency_ms: float = Field(..., description="Guardrails 延迟")


class QualityMetrics(BaseModel):
    """质量指标：用于监控输出质量"""
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="记录时间"
    )

    # 对话质量
    avg_conversation_score: float = Field(..., description="平均对话质量分")
    satisfaction_rate: float = Field(..., description="满意度")

    # 转化指标
    conversion_rate: float = Field(..., description="转化率")
    avg_funnel_progression: float = Field(..., description="平均漏斗推进进度")

    # 合规指标
    compliance_violation_rate: float = Field(..., description="合规违规率")
    risk_warning_coverage: float = Field(..., description="风险提示覆盖率")
