"""
State Models - 核心数据模型定义
使用 Pydantic 实现强类型检查，防止幻觉
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class CustomerTemperature(str):
    """
    客户温度：反映客户当前的购买意愿和情绪状态
    """
    ALLOWED_VALUES = ["cold", "neutral", "warm", "hot"]

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if v not in cls.ALLOWED_VALUES:
            raise ValueError(f"CustomerTemperature must be one of {cls.ALLOWED_VALUES}")
        return v


class FunnelStage(str):
    """
    漏斗阶段：客户在购买旅程中的当前位置
    """
    ALLOWED_VALUES = [
        "awareness",      # 认知阶段：初次接触
        "interest",       # 兴趣阶段：对产品表现出兴趣
        "consideration",  # 考虑阶段：开始对比和思考
        "intent",         # 意图阶段：明确表达购买意愿
        "evaluation",     # 评估阶段：讨论细节、条款、价格
        "purchase"        # 购买阶段：准备签约或已签约
    ]

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if v not in cls.ALLOWED_VALUES:
            raise ValueError(f"FunnelStage must be one of {cls.ALLOWED_VALUES}")
        return v


class DISCType(str):
    """
    DISC 性格类型：描述客户的核心行为风格
    """
    ALLOWED_VALUES = ["D", "I", "S", "C", "unknown"]

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if v not in cls.ALLOWED_VALUES:
            raise ValueError(f"DISCType must be one of {cls.ALLOWED_VALUES}")
        return v


class UserProfile(BaseModel):
    """
    用户画像：包含 DISC 性格侧写和互动历史信息

    这是系统的核心数据结构，用于个性化话术生成
    """
    user_id: str = Field(..., description="用户唯一标识")
    disc_type: DISCType = Field(default="unknown", description="DISC 性格类型")
    secondary_type: Optional[DISCType] = Field(None, description="次要性格类型")
    interaction_stage: FunnelStage = Field(
        default="awareness",
        description="当前互动阶段"
    )

    # 元数据
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="画像创建时间"
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="最后更新时间"
    )

    # 扩展信息（可选）
    interaction_style: Optional[str] = Field(None, description="互动风格建议")
    decision_factors: list[str] = Field(
        default_factory=list,
        description="影响决策的关键因素"
    )
    risk_aversion: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="风险厌恶程度"
    )

    # 证据链（用于解释 DISC 判断）
    evidence: list[dict] = Field(
        default_factory=list,
        description="支持当前 DISC 判断的对话证据"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_12345",
                "disc_type": "I",
                "secondary_type": "S",
                "interaction_stage": "interest",
                "interaction_style": "热情互动，多讲故事，建立情感连接",
                "decision_factors": ["品牌声誉", "服务保障", "收益演示"],
                "risk_aversion": "medium",
                "evidence": [
                    {
                        "quote": "我想了解一下这个产品",
                        "reason": "开放性问题，表现出探索意愿"
                    }
                ]
            }
        }


class FunnelState(BaseModel):
    """
    漏斗状态：跟踪客户在销售漏斗中的实时状态
    由 Intent Classifier 异步更新
    """
    user_id: str = Field(..., description="用户唯一标识")

    # 核心状态
    customer_temperature: Literal["cold", "neutral", "warm", "hot"] = Field(
        default="neutral",
        description="客户温度：反映当前购买意愿"
    )
    funnel_stage: FunnelStage = Field(
        default="awareness",
        description="漏斗阶段"
    )

    # 置信度和元数据
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="状态判断的置信度"
    )
    reasoning: str = Field(default="", description="状态判断的理由")
    updated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="状态更新时间"
    )

    # 历史追踪
    previous_stages: list[FunnelStage] = Field(
        default_factory=list,
        description="历史阶段记录"
    )
    temperature_history: list[tuple[str, str]] = Field(
        default_factory=list,
        description="温度变化历史 [(temperature, timestamp), ...]"
    )

    def transition_to(self, new_stage: FunnelStage, new_temperature: str, reasoning: str = ""):
        """转换到新阶段，记录历史"""
        # 记录历史
        self.previous_stages.append(self.funnel_stage)
        self.temperature_history.append((self.customer_temperature, datetime.utcnow().isoformat()))

        # 更新状态
        self.funnel_stage = new_stage
        self.customer_temperature = new_temperature
        self.reasoning = reasoning
        self.updated_at = datetime.utcnow().isoformat()

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_12345",
                "customer_temperature": "warm",
                "funnel_stage": "consideration",
                "confidence": 0.85,
                "reasoning": "客户主动询问保费和保障范围，表现出明确的购买意向",
                "previous_stages": ["awareness", "interest"],
                "temperature_history": [
                    ("neutral", "2025-01-01T10:00:00"),
                    ("warm", "2025-01-01T10:15:00")
                ]
            }
        }


class ConversationTurn(BaseModel):
    """单轮对话记录"""
    role: Literal["user", "assistant"] = Field(..., description="发言角色")
    content: str = Field(..., description="对话内容")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="时间戳"
    )
    metadata: Optional[dict] = Field(None, description="附加元数据")


class SessionContext(BaseModel):
    """会话上下文：包含完整的对话会话信息"""
    session_id: str = Field(..., description="会话唯一标识")
    user_id: str = Field(..., description="用户 ID")

    # 对话历史
    turns: list[ConversationTurn] = Field(
        default_factory=list,
        description="对话轮次列表"
    )

    # 状态快照
    state_snapshot: Optional[FunnelState] = Field(None, description="当前状态快照")
    profile_snapshot: Optional[UserProfile] = Field(None, description="用户画像快照")

    # 会话元数据
    started_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="会话开始时间"
    )
    ended_at: Optional[str] = Field(None, description="会话结束时间")
    outcome: Optional[Literal["converted", "lost", "ongoing"]] = Field(
        None,
        description="会话结果"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_abc123",
                "user_id": "user_12345",
                "turns": [],
                "outcome": "ongoing"
            }
        }
