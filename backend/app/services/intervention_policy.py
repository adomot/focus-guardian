"""介入の発火判断・再介入抑制・結果評価 (要件 3.3, 3.4, 4.1, 4.4, 4.5, 5.1〜5.3)。

LLM を使わない決定的ロジック。セッション状態を入力に、
更新後の状態と発火すべき介入・評価結果を返す純粋関数として実装する。
"""

import uuid
from dataclasses import dataclass

from app.models.config import MonitoringConfig
from app.models.monitoring import (
    HabitPhase,
    HabitState,
    InterventionDirective,
    JudgmentResult,
    JudgmentState,
    SessionState,
)


@dataclass(frozen=True)
class PolicyDecision:
    session: SessionState
    directive: InterventionDirective | None
    evaluation_result: str | None  # 直前介入の評価 "returned" / "not_returned"
    evaluated_intervention_id: str | None


class InterventionPolicy:
    def __init__(self, consecutive_threshold: int = 2, confidence_threshold: float = 0.7) -> None:
        self._consecutive_threshold = consecutive_threshold
        self._confidence_threshold = confidence_threshold

    def decide(
        self, session: SessionState, config: MonitoringConfig, judgment: JudgmentResult
    ) -> PolicyDecision:
        session = session.model_copy(deep=True)

        evaluation_result, evaluated_id = self._evaluate_pending(session, judgment)
        directive = None

        if judgment.state == JudgmentState.FOCUSED:
            self._on_focused(session)
        elif judgment.state == JudgmentState.ABSENT:
            self._on_absent(session)
        elif judgment.state == JudgmentState.HABIT and judgment.habit_id:
            directive = self._on_habit(session, config, judgment)

        return PolicyDecision(
            session=session,
            directive=directive,
            evaluation_result=evaluation_result,
            evaluated_intervention_id=evaluated_id,
        )

    def _evaluate_pending(
        self, session: SessionState, judgment: JudgmentResult
    ) -> tuple[str | None, str | None]:
        """介入直後の判定で作業復帰を評価する (要件 5.1, 5.2)"""
        if session.pending_evaluation is None:
            return None, None
        intervention_id = session.pending_evaluation
        session.pending_evaluation = None
        result = "returned" if judgment.state == JudgmentState.FOCUSED else "not_returned"
        return result, intervention_id

    def _on_focused(self, session: SessionState) -> None:
        """集中復帰: 全カウンタをリセットし、発火済み悪習慣を再武装する (要件 4.5, 5.3)"""
        session.counters.focused += 1
        for state in session.habit_states.values():
            state.consecutive_count = 0
            state.phase = HabitPhase.ARMED

    def _on_absent(self, session: SessionState) -> None:
        """不在: カウンタをリセットし介入は発火しない (要件 3.4)"""
        for state in session.habit_states.values():
            state.consecutive_count = 0

    def _on_habit(
        self, session: SessionState, config: MonitoringConfig, judgment: JudgmentResult
    ) -> InterventionDirective | None:
        habit_id = judgment.habit_id
        assert habit_id is not None
        session.counters.habit_detected += 1

        if judgment.confidence < self._confidence_threshold:
            return None  # 低確信度はカウントに含めない (判定保留)

        state = session.habit_states.setdefault(habit_id, HabitState())
        for other_id, other in session.habit_states.items():
            if other_id != habit_id:
                other.consecutive_count = 0

        if state.phase == HabitPhase.FIRED:
            return None  # 同一悪習慣の継続中は再介入しない (要件 4.4)

        state.consecutive_count += 1
        if state.consecutive_count < self._consecutive_threshold:
            return None

        habit = next((h for h in config.habits if h.habit_id == habit_id), None)
        if habit is None:
            return None

        state.phase = HabitPhase.FIRED
        state.consecutive_count = 0
        intervention_id = uuid.uuid4().hex
        session.pending_evaluation = intervention_id
        session.counters.interventions += 1
        return InterventionDirective(
            intervention_id=intervention_id,
            habit_id=habit_id,
            method=habit.notification.method,
            audio_url=habit.notification.audio_url,
            delivered_by="speaker",  # 実行結果に応じて MonitoringService が上書きする
        )
