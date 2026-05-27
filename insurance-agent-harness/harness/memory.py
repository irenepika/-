"""
Memory Manager - 上下文管理器
拼接当前会话与历史 DISC 画像
"""
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from schemas.state_models import UserProfile, FunnelState, CustomerTemperature


class MemoryManager:
    """
    上下文管理器：负责管理用户画像、对话历史和状态存储
    支持从文件系统或数据库读取/写入数据
    """

    def __init__(self, base_path: str = "./output"):
        self.base_path = Path(base_path)
        self.user_profiles_dir = self.base_path / "user_profiles"
        self.logs_dir = self.base_path / "logs"

        # 确保目录存在
        self.user_profiles_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # 内存缓存（生产环境应替换为 Redis 或数据库）
        self._profile_cache = {}
        self._history_cache = {}
        self._state_cache = {}

    async def get_user_profile(self, user_id: str) -> UserProfile:
        """
        获取用户画像（包含 DISC 性格侧写）

        Args:
            user_id: 用户唯一标识

        Returns:
            UserProfile 对象
        """
        # 先检查缓存
        if user_id in self._profile_cache:
            return self._profile_cache[user_id]

        # 从文件读取
        profile_path = self.user_profiles_dir / f"{user_id}.json"

        if profile_path.exists():
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                profile = UserProfile(**data)
        else:
            # 创建默认画像
            profile = UserProfile(
                user_id=user_id,
                disc_type="unknown",
                interaction_stage="awareness",
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat()
            )

        # 更新缓存
        self._profile_cache[user_id] = profile
        return profile

    async def update_user_profile(self, user_id: str, profile: UserProfile):
        """
        更新用户画像到持久化存储

        Args:
            user_id: 用户唯一标识
            profile: 更新后的 UserProfile
        """
        profile_path = self.user_profiles_dir / f"{user_id}.json"

        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile.dict(), f, ensure_ascii=False, indent=2)

        # 更新缓存
        self._profile_cache[user_id] = profile

    async def get_conversation_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        获取历史对话记录

        Args:
            user_id: 用户唯一标识
            limit: 返回最近 N 轮对话

        Returns:
            对话历史列表，格式：[{"role": "user", "content": "..."}, ...]
        """
        # 从缓存获取
        if user_id in self._history_cache:
            return self._history_cache[user_id][-limit:]

        # TODO: 从持久化存储读取完整历史
        return []

    async def append_conversation_turn(
        self,
        user_id: str,
        user_message: str,
        assistant_message: str,
        session_id: Optional[str] = None
    ):
        """
        添加一轮对话到历史记录

        Args:
            user_id: 用户唯一标识
            user_message: 用户消息
            assistant_message: Assistant 回复
            session_id: 会话 ID（可选）
        """
        if user_id not in self._history_cache:
            self._history_cache[user_id] = []

        self._history_cache[user_id].extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message}
        ])

    async def get_conversation_window(
        self,
        user_id: str,
        window_size: int = 5
    ) -> List[Dict[str, str]]:
        """
        获取最近的对话窗口（用于意图分类）

        Args:
            user_id: 用户唯一标识
            window_size: 窗口大小（轮数）

        Returns:
            最近 N 轮对话
        """
        history = await self.get_conversation_history(user_id)
        return history[-window_size:]

    async def get_current_state(self, user_id: str) -> Dict[str, Any]:
        """
        获取当前状态（客户温度、漏斗阶段等）

        Args:
            user_id: 用户唯一标识

        Returns:
            状态字典
        """
        return self._state_cache.get(user_id, {
            "customer_temperature": "neutral",
            "funnel_stage": "awareness"
        })

    async def update_state(self, user_id: str, new_state: Dict[str, Any]):
        """
        更新用户状态

        Args:
            user_id: 用户唯一标识
            new_state: 新的状态数据
        """
        if user_id not in self._state_cache:
            self._state_cache[user_id] = {}

        self._state_cache[user_id].update(new_state)

    async def log_interaction(
        self,
        user_id: str,
        user_input: str,
        assistant_response: str,
        state: Dict[str, Any],
        session_id: Optional[str] = None
    ):
        """
        记录完整的交互日志（用于审计和离线分析）

        Args:
            user_id: 用户唯一标识
            user_input: 用户输入
            assistant_response: Assistant 回复
            state: 当时的状态
            session_id: 会话 ID
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "session_id": session_id,
            "user_input": user_input,
            "assistant_response": assistant_response,
            "state": state,
            "profile": self._profile_cache.get(user_id, {}).dict() if user_id in self._profile_cache else None
        }

        # 写入日志文件（按日期分隔）
        log_file = self.logs_dir / f"run_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
