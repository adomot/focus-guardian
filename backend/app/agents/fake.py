from app.models.config import DetectionCondition, MonitoringConfig
from app.models.monitoring import Frame, JudgmentResult, JudgmentState


class FakeStructuringAgent:
    """ローカル開発・テスト用。入力テキストから決定的に検知条件を生成する"""

    async def structure_habit(self, raw_text: str) -> DetectionCondition:
        label = raw_text.strip().rstrip("。")
        return DetectionCondition(
            habit_label=label,
            visual_cues=[f"{label} をしている様子が画像から確認できる"],
            judge_hint=f"人物が「{label}」に該当する行動をしているか",
        )


class FakeJudgeAgent:
    """ローカル開発・テスト用。既定は focused。

    フレーム先頭 100 バイト内のマーカーで判定を切り替えられる
    (JPEG マジックバイトの後に埋め込む想定):
    b"HABIT:<habit_id>:" は該当悪習慣、b"ABSENT" は不在。
    """

    async def judge(self, frame: Frame, config: MonitoringConfig) -> JudgmentResult:
        head = frame.jpeg_bytes[:100]
        if b"ABSENT" in head:
            return JudgmentResult(
                state=JudgmentState.ABSENT, confidence=0.9, reason="人物が写っていません"
            )
        marker_at = head.find(b"HABIT:")
        if marker_at >= 0:
            habit_id = head[marker_at:].split(b":", 2)[1].decode()
            return JudgmentResult(
                state=JudgmentState.HABIT,
                habit_id=habit_id,
                confidence=0.9,
                reason="悪習慣の行動を検知しました",
            )
        return JudgmentResult(
            state=JudgmentState.FOCUSED, confidence=0.9, reason="作業に集中しています"
        )
