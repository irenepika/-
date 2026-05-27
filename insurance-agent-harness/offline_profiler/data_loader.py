"""
Data Loader - 离线数据加载器
模拟从历史数据库/日志中拉取指定 userid 的全量对话
"""
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime


class DataLoader:
    """
    离线数据加载器：从历史日志、数据库中提取用户的完整对话记录
    用于离线分析和用户画像生成
    """

    def __init__(self, logs_dir: str = "./output/logs"):
        self.logs_dir = Path(logs_dir)

    def load_user_history(
        self,
        user_id: str,
        date_range: Optional[tuple[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        加载指定用户的历史对话记录

        Args:
            user_id: 用户唯一标识
            date_range: 日期范围 (start_date, end_date)，格式：YYYYMMDD

        Returns:
            完整的对话历史列表
        """
        conversations = []

        # 如果指定了日期范围，只读取指定日期的日志
        if date_range:
            start_date, end_date = date_range
            log_files = self._get_log_files_in_range(start_date, end_date)
        else:
            # 否则读取所有日志文件
            log_files = sorted(self.logs_dir.glob("run_*.jsonl"))

        # 从日志文件中提取该用户的对话
        for log_file in log_files:
            if not log_file.exists():
                continue

            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        if log_entry.get("user_id") == user_id:
                            conversations.append(log_entry)
                    except json.JSONDecodeError:
                        continue

        return conversations

    def load_batch_users(
        self,
        user_ids: List[str],
        date_range: Optional[tuple[str, str]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        批量加载多个用户的历史记录

        Args:
            user_ids: 用户 ID 列表
            date_range: 日期范围

        Returns:
            {user_id: conversations} 的字典
        """
        return {
            user_id: self.load_user_history(user_id, date_range)
            for user_id in user_ids
        }

    def load_recent_interactions(
        self,
        user_id: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        加载最近 N 天的互动记录

        Args:
            user_id: 用户唯一标识
            days: 天数

        Returns:
            最近的对话记录
        """
        end_date = datetime.now()
        start_date = end_date.replace(day=end_date.day - days)

        date_range = (
            start_date.strftime("%Y%m%d"),
            end_date.strftime("%Y%m%d")
        )

        return self.load_user_history(user_id, date_range)

    def get_active_users(
        self,
        date_range: Optional[tuple[str, str]] = None,
        min_interactions: int = 1
    ) -> List[str]:
        """
        获取活跃用户列表（满足最小互动次数）

        Args:
            date_range: 日期范围
            min_interactions: 最小互动次数

        Returns:
            用户 ID 列表
        """
        user_interaction_counts = {}

        log_files = sorted(self.logs_dir.glob("run_*.jsonl"))

        for log_file in log_files:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        user_id = log_entry.get("user_id")
                        if user_id:
                            user_interaction_counts[user_id] = \
                                user_interaction_counts.get(user_id, 0) + 1
                    except json.JSONDecodeError:
                        continue

        # 筛选满足条件的用户
        active_users = [
            user_id for user_id, count in user_interaction_counts.items()
            if count >= min_interactions
        ]

        return active_users

    def _get_log_files_in_range(
        self,
        start_date: str,
        end_date: str
    ) -> List[Path]:
        """
        获取指定日期范围内的日志文件

        Args:
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)

        Returns:
            日志文件路径列表
        """
        log_files = []
        current = start_date

        while current <= end_date:
            log_file = self.logs_dir / f"run_{current}.jsonl"
            if log_file.exists():
                log_files.append(log_file)
            # 递增日期
            current = self._increment_date(current)

        return log_files

    @staticmethod
    def _increment_date(date_str: str) -> str:
        """日期递增一天"""
        from datetime import datetime, timedelta
        date = datetime.strptime(date_str, "%Y%m%d")
        next_date = date + timedelta(days=1)
        return next_date.strftime("%Y%m%d")


class MockDataGenerator:
    """
    Mock 数据生成器：用于测试和演示
    生成模拟的对话记录
    """

    @staticmethod
    def generate_mock_conversations(
        user_id: str,
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        生成模拟对话记录

        Args:
            user_id: 用户 ID
            count: 对话轮数

        Returns:
            模拟对话列表
        """
        mock_templates = [
            {
                "user": "我想了解一下保险产品",
                "assistant": "您好！我可以为您介绍我们的保险产品。请问您主要关注哪些方面的保障？"
            },
            {
                "user": "重疾险怎么样",
                "assistant": "重疾险是非常实用的保障产品，可以在确诊重大疾病时提供一笔保险金，用于治疗和收入补偿。"
            },
            {
                "user": "保费大概多少",
                "assistant": "保费取决于您的年龄、性别和保额。我可以帮您具体计算一下。"
            }
        ]

        conversations = []
        for i in range(count):
            template = mock_templates[i % len(mock_templates)]
            conversations.append({
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "user_input": template["user"],
                "assistant_response": template["assistant"],
                "session_id": f"session_{i}"
            })

        return conversations
