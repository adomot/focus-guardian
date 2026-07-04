"""介入ポリシーの発火判断テスト (要件 3.3, 3.4, 4.1, 4.4, 4.5, 5.1〜5.3)"""

from datetime import UTC, datetime

from app.models.config import Habit, MonitoringConfig, Notification
from app.models.monitoring import (
    HabitPhase,
    JudgmentResult,
    JudgmentState,
    SessionState,
)
from app.services.intervention_policy import InterventionPolicy


def make_config() -> MonitoringConfig:
    return MonitoringConfig(
        config_id="c1",
        goal="目標",
        habits=[
            Habit(
                habit_id="habit_1",
                label="スマホいじり",
                visual_cues=["スマホを持っている"],
                judge_hint="スマホ操作中か",
                notification=Notification(
                    method="bgm", bgm_track_id="focus", audio_url="https://a/bgm.mp3"
                ),
            ),
            Habit(
                habit_id="habit_2",
                label="居眠り",
                visual_cues=["目を閉じている"],
                judge_hint="居眠り中か",
                notification=Notification(
                    method="speech", phrase="起きてください", audio_url="https://a/p.mp3"
                ),
            ),
        ],
        created_at=datetime.now(UTC),
    )


def make_session() -> SessionState:
    return SessionState(session_id="s1", config_id="c1", started_at=datetime.now(UTC))


def habit(habit_id: str = "habit_1", confidence: float = 0.9) -> JudgmentResult:
    return JudgmentResult(
        state=JudgmentState.HABIT, habit_id=habit_id, confidence=confidence, reason="r"
    )


def focused() -> JudgmentResult:
    return JudgmentResult(state=JudgmentState.FOCUSED, confidence=0.9, reason="r")


def absent() -> JudgmentResult:
    return JudgmentResult(state=JudgmentState.ABSENT, confidence=0.9, reason="r")


def make_policy() -> InterventionPolicy:
    return InterventionPolicy(consecutive_threshold=2, confidence_threshold=0.7)


class TestFiring:
    def test_fires_after_consecutive_threshold(self):
        """連続2回で発火 (3.3, 4.1)"""
        policy, config = make_policy(), make_config()
        session = make_session()

        d1 = policy.decide(session, config, habit())
        assert d1.directive is None

        d2 = policy.decide(d1.session, config, habit())
        assert d2.directive is not None
        assert d2.directive.habit_id == "habit_1"
        assert d2.directive.method == "bgm"
        assert d2.session.habit_states["habit_1"].phase == HabitPhase.FIRED
        assert d2.session.pending_evaluation == d2.directive.intervention_id

    def test_low_confidence_not_counted(self):
        """確信度 0.7 未満はカウントしない"""
        policy, config = make_policy(), make_config()
        session = make_session()

        d1 = policy.decide(session, config, habit())
        d2 = policy.decide(d1.session, config, habit(confidence=0.5))
        assert d2.directive is None
        d3 = policy.decide(d2.session, config, habit())
        assert d3.directive is not None  # 低確信度はリセットもしない

    def test_no_refire_while_habit_continues(self):
        """同一悪習慣の継続中は再介入しない (4.4)"""
        policy, config = make_policy(), make_config()
        session = make_session()

        d = policy.decide(session, config, habit())
        d = policy.decide(d.session, config, habit())
        assert d.directive is not None

        d = policy.decide(d.session, config, habit())
        assert d.directive is None
        d = policy.decide(d.session, config, habit())
        assert d.directive is None

    def test_refires_after_focus_recovery(self):
        """集中復帰後の再検知では改めて1回介入する (4.5)"""
        policy, config = make_policy(), make_config()
        session = make_session()

        d = policy.decide(session, config, habit())
        d = policy.decide(d.session, config, habit())
        assert d.directive is not None

        d = policy.decide(d.session, config, focused())
        assert d.session.habit_states["habit_1"].phase == HabitPhase.ARMED

        d = policy.decide(d.session, config, habit())
        assert d.directive is None
        d = policy.decide(d.session, config, habit())
        assert d.directive is not None

    def test_absent_resets_count_and_never_fires(self):
        """不在はカウンタをリセットし発火しない (3.4)"""
        policy, config = make_policy(), make_config()
        session = make_session()

        d = policy.decide(session, config, habit())
        d = policy.decide(d.session, config, absent())
        assert d.directive is None

        d = policy.decide(d.session, config, habit())
        assert d.directive is None  # カウントは1からやり直し
        d = policy.decide(d.session, config, habit())
        assert d.directive is not None

    def test_other_habit_resets_competing_count(self):
        """別の悪習慣を検知したら他方の連続カウントはリセット"""
        policy, config = make_policy(), make_config()
        session = make_session()

        d = policy.decide(session, config, habit("habit_1"))
        d = policy.decide(d.session, config, habit("habit_2"))
        assert d.directive is None
        d = policy.decide(d.session, config, habit("habit_2"))
        assert d.directive is not None
        assert d.directive.habit_id == "habit_2"
        assert d.directive.method == "speech"


class TestEvaluation:
    def test_returned_when_focused_after_intervention(self):
        """介入直後に集中していれば returned (5.1, 5.2)"""
        policy, config = make_policy(), make_config()
        session = make_session()

        d = policy.decide(session, config, habit())
        d = policy.decide(d.session, config, habit())
        intervention_id = d.directive.intervention_id

        d = policy.decide(d.session, config, focused())
        assert d.evaluation_result == "returned"
        assert d.evaluated_intervention_id == intervention_id
        assert d.session.pending_evaluation is None

    def test_not_returned_when_habit_continues(self):
        d = None
        policy, config = make_policy(), make_config()
        session = make_session()

        d = policy.decide(session, config, habit())
        d = policy.decide(d.session, config, habit())
        d = policy.decide(d.session, config, habit())
        assert d.evaluation_result == "not_returned"

    def test_no_intervention_while_focused(self):
        """集中継続中は介入しない (5.3)"""
        policy, config = make_policy(), make_config()
        session = make_session()

        d = policy.decide(session, config, focused())
        assert d.directive is None
        d = policy.decide(d.session, config, focused())
        assert d.directive is None
        assert d.session.counters.focused == 2
