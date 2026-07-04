from typing import Protocol

from app.models.config import DetectionCondition, MonitoringConfig
from app.models.monitoring import Frame, JudgmentResult


class AgentError(Exception):
    """エージェント呼び出しの失敗 (API エラー・スキーマ逸脱)。

    判定側は要件 3.5 (記録して次周期で再試行)、
    ヒアリング側は要件 1.10 (同一質問の再提示) のエラー経路で処理する。
    """


class StructuringAgentPort(Protocol):
    async def structure_habit(self, raw_text: str) -> DetectionCondition: ...


class JudgeAgentPort(Protocol):
    async def judge(self, frame: Frame, config: MonitoringConfig) -> JudgmentResult: ...
