"""
Core Loop - Agent 主循环
接收输入 -> 调出画像 -> 运行拦截 -> 生成回复 -> 异步打标
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from agents.sales_actor import SalesActor
from agents.intent_classifier import IntentClassifier
from harness.guardrails import Guardrails
from harness.memory import MemoryManager
from harness.tools.registry import ToolRegistry
from schemas.state_models import UserProfile, FunnelState


class AgentCoreLoop:
    """
    Agent 核心循环：编排所有组件，实现实时对话与异步状态更新
    """

    def __init__(
        self,
        sales_actor: Optional[SalesActor] = None,
        intent_classifier: Optional[IntentClassifier] = None,
        guardrails: Optional[Guardrails] = None,
        memory_manager: Optional[MemoryManager] = None,
        tool_registry: Optional[ToolRegistry] = None
    ):
        self.sales_actor = sales_actor or SalesActor()
        self.intent_classifier = intent_classifier or IntentClassifier()
        self.guardrails = guardrails or Guardrails()
        self.memory_manager = memory_manager or MemoryManager()
        self.tool_registry = tool_registry or ToolRegistry()

    async def chat(
        self,
        user_id: str,
        user_input: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        主聊天入口：执行完整的实时对话循环

        流程：
        1. 从 Memory 拉取用户画像和历史对话
        2. Guardrails 进行在线合规拦截
        3. Sales Actor 生成回复（可能调用工具）
        4. 更新对话历史到 Memory
        5. 异步触发状态更新（不阻塞主流程）
        6. 记录审计日志

        Args:
            user_id: 用户唯一标识
            user_input: 用户输入文本
            session_id: 会话 ID（可选，用于多轮对话追踪）

        Returns:
            包含回复内容、更新后状态等信息的字典
        """
        # Step 1: 从 Memory 拉取用户画像和历史
        user_profile = await self.memory_manager.get_user_profile(user_id)
        conversation_history = await self.memory_manager.get_conversation_history(user_id)
        current_state = await self.memory_manager.get_current_state(user_id)

        # Step 2: Guardrails 合规拦截
        guardrails_result = self.guardrails.check_input(user_input)
        if not guardrails_result["allowed"]:
            return {
                "response": guardrails_result["block_message"],
                "blocked": True,
                "reason": guardrails_result["reason"],
                "timestamp": datetime.utcnow().isoformat()
            }

        # Step 3: Sales Actor 生成回复
        available_tools = self.tool_registry.get_openai_tools()
        response = self.sales_actor.generate_response(
            user_input=user_input,
            user_profile=user_profile,
            conversation_history=conversation_history,
            available_tools=available_tools
        )

        # Step 4: 更新对话历史到 Memory
        await self.memory_manager.append_conversation_turn(
            user_id=user_id,
            user_message=user_input,
            assistant_message=response,
            session_id=session_id
        )

        # Step 5: 异步触发状态更新（不阻塞主流程）
        asyncio.create_task(
            self._async_update_state(user_id, conversation_history, user_input, response)
        )

        # Step 6: 记录审计日志
        await self.memory_manager.log_interaction(
            user_id=user_id,
            user_input=user_input,
            assistant_response=response,
            state=current_state,
            session_id=session_id
        )

        return {
            "response": response,
            "blocked": False,
            "user_id": user_id,
            "session_id": session_id,
            "current_disc_type": user_profile.disc_type,
            "current_temperature": current_state.get("customer_temperature", "unknown"),
            "current_funnel_stage": current_state.get("funnel_stage", "unknown"),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _async_update_state(
        self,
        user_id: str,
        conversation_history: list[Dict[str, str]],
        user_input: str,
        assistant_response: str
    ):
        """
        异步状态更新：在后台进行意图分类和状态更新
        不阻塞主对话流程
        """
        try:
            # 获取最近的对话窗口（最近 N 轮）
            recent_window = await self.memory_manager.get_conversation_window(
                user_id, window_size=5
            )

            # 获取当前状态
            current_state = await self.memory_manager.get_current_state(user_id)

            # 调用 Intent Classifier 进行状态判定
            classification_result = self.intent_classifier.classify_conversation_window(
                conversation_window=recent_window,
                previous_state=current_state
            )

            # 更新状态到 Memory
            await self.memory_manager.update_state(
                user_id=user_id,
                new_state=classification_result
            )

        except Exception as e:
            # 异步任务中的错误不应影响主流程
            print(f"Async state update failed for user {user_id}: {str(e)}")

    def run_batch_processing(self, user_ids: list[str]):
        """
        批量处理模式：用于离线处理多个用户
        例如：重新分析所有历史对话，更新用户画像
        """
        # TODO: 实现批量处理逻辑
        pass
