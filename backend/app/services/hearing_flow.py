"""固定フローヒアリングのステートマシン (要件 1.1〜1.10)。

フロー制御は決定的コードが担い、LLM は悪習慣の構造化 (1.8) のみに使う。
想定外の入力では状態を変更せず同一質問を再提示する (1.10)。
"""

import logging
import uuid
from datetime import UTC, datetime

from app.agents.base import AgentError, StructuringAgentPort
from app.models.config import Habit, MonitoringConfig, Notification
from app.models.hearing import (
    Choice,
    DraftHabit,
    HearingState,
    HearingStep,
    HearingTurn,
    UserInput,
)
from app.repositories.base import ConfigRepository, HearingRepository
from app.services.speech_assets import BGM_CATALOG, SpeechAssetService, get_bgm_track

logger = logging.getLogger(__name__)

NOTIFY_CHOICES = [
    Choice(choice_id="bgm", label="BGMを流す"),
    Choice(choice_id="speech", label="言葉で通知する"),
]
DONE_CHOICE = Choice(choice_id="done", label="もう大丈夫")

# 悪習慣の定番レコメンド (要件 1.2 補助)。選択でも自由入力でも受け付ける
HABIT_RECOMMENDATIONS = [
    Choice(choice_id="rec_smartphone", label="ついスマホをいじってしまう"),
    Choice(choice_id="rec_nap", label="つい居眠りをしてしまう"),
    Choice(choice_id="rec_snack", label="お菓子をダラダラ食べてしまう"),
]


class HearingNotFoundError(Exception):
    pass


class HearingFlowService:
    def __init__(
        self,
        hearings: HearingRepository,
        configs: ConfigRepository,
        structuring: StructuringAgentPort,
        assets: SpeechAssetService,
    ) -> None:
        self._hearings = hearings
        self._configs = configs
        self._structuring = structuring
        self._assets = assets

    async def start(self) -> HearingTurn:
        state = HearingState(
            hearing_id=uuid.uuid4().hex,
            step=HearingStep.GOAL,
            updated_at=datetime.now(UTC),
        )
        await self._hearings.save(state)
        return self._turn(state, "実現したい目標はありますか？")

    async def reply(self, hearing_id: str, user_input: UserInput) -> HearingTurn:
        state = await self._hearings.get(hearing_id)
        if state is None:
            raise HearingNotFoundError(hearing_id)

        handler = {
            HearingStep.GOAL: self._on_goal,
            HearingStep.HABIT: self._on_habit,
            HearingStep.NOTIFY_TYPE: self._on_notify_type,
            HearingStep.BGM_SELECT: self._on_bgm_select,
            HearingStep.PHRASE: self._on_phrase,
            HearingStep.MORE_HABITS: self._on_more_habits,
            HearingStep.DONE: self._on_done,
        }[state.step]
        turn = await handler(state, user_input)
        state.updated_at = datetime.now(UTC)
        await self._hearings.save(state)
        return turn

    # --- ステップハンドラ ---

    async def _on_goal(self, state: HearingState, user_input: UserInput) -> HearingTurn:
        text = (user_input.text or "").strip()
        if not text:
            return self._turn(state, "実現したい目標はありますか？")
        state.goal = text
        state.step = HearingStep.HABIT
        return self._turn(
            state,
            "承知しました！では、それの障壁となっている悪習慣を教えてください。",
            choices=self._habit_recommendations(state),
        )

    async def _on_habit(self, state: HearingState, user_input: UserInput) -> HearingTurn:
        return await self._accept_habit(
            state,
            user_input,
            reprompt="それの障壁となっている悪習慣を教えてください。",
            reprompt_choices=self._habit_recommendations(state),
        )

    async def _accept_habit(
        self,
        state: HearingState,
        user_input: UserInput,
        reprompt: str,
        reprompt_choices: list[Choice] | None = None,
    ) -> HearingTurn:
        text = self._resolve_habit_text(user_input)
        if not text:
            return self._turn(state, reprompt, choices=reprompt_choices)
        try:
            condition = await self._structuring.structure_habit(text)
        except AgentError:
            logger.warning("habit structuring failed; re-prompting", exc_info=True)
            return self._turn(
                state, f"うまく理解できませんでした。{reprompt}", choices=reprompt_choices
            )
        state.current_habit = DraftHabit(
            label=condition.habit_label,
            visual_cues=condition.visual_cues,
            judge_hint=condition.judge_hint,
        )
        state.step = HearingStep.NOTIFY_TYPE
        return self._turn(
            state,
            "承知しました。それを検知した場合はどのような通知をしましょうか。",
            choices=NOTIFY_CHOICES,
            input_mode="choices",
        )

    async def _on_notify_type(self, state: HearingState, user_input: UserInput) -> HearingTurn:
        choice = user_input.choice_id
        if choice == "bgm":
            state.step = HearingStep.BGM_SELECT
            return self._turn(
                state,
                "わかりました。では、BGMを流すようにしますね。どのBGMが良いでしょうか。",
                choices=[Choice(choice_id=t.track_id, label=t.label) for t in BGM_CATALOG],
                input_mode="choices",
            )
        if choice == "speech":
            state.step = HearingStep.PHRASE
            return self._turn(state, "どのような言葉で通知しましょう？")
        return self._turn(
            state,
            "それを検知した場合はどのような通知をしましょうか。",
            choices=NOTIFY_CHOICES,
            input_mode="choices",
        )

    async def _on_bgm_select(self, state: HearingState, user_input: UserInput) -> HearingTurn:
        track = get_bgm_track(user_input.choice_id or "")
        if track is None or state.current_habit is None:
            return self._turn(
                state,
                "どのBGMが良いでしょうか。",
                choices=[Choice(choice_id=t.track_id, label=t.label) for t in BGM_CATALOG],
                input_mode="choices",
            )
        state.current_habit.notification = Notification(
            method="bgm",
            bgm_track_id=track.track_id,
            audio_url=self._assets.bgm_url(track.track_id),
        )
        self._commit_current_habit(state)
        return self._more_habits_turn(state, f"わかりました。{track.label}を設定しますね。")

    async def _on_phrase(self, state: HearingState, user_input: UserInput) -> HearingTurn:
        text = (user_input.text or "").strip()
        if not text or state.current_habit is None:
            return self._turn(state, "どのような言葉で通知しましょう？")
        try:
            audio_url = await self._assets.synthesize_phrase(text)
        except Exception:
            logger.exception("phrase synthesis failed; re-prompting")
            return self._turn(
                state, "音声の準備に失敗しました。どのような言葉で通知しましょう？"
            )
        state.current_habit.notification = Notification(
            method="speech", phrase=text, audio_url=audio_url
        )
        self._commit_current_habit(state)
        return self._more_habits_turn(state, "承知しました。そのような言葉で伝えます。")

    async def _on_more_habits(self, state: HearingState, user_input: UserInput) -> HearingTurn:
        if user_input.choice_id == DONE_CHOICE.choice_id:
            config = await self._save_config(state)
            state.step = HearingStep.DONE
            summary = self._config_summary(config)
            return self._turn(
                state,
                "教えていただきありがとうございました。"
                f"以下の内容で設定しました。\n{summary}\n修正したい時はまたお声かけください！",
                done=True,
                config_id=config.config_id,
            )
        if self._resolve_habit_text(user_input):
            return await self._accept_habit(
                state,
                user_input,
                reprompt="他に何か悪習慣はありますか？",
                reprompt_choices=self._more_habits_choices(state),
            )
        return self._more_habits_turn(state, "")

    async def _on_done(self, state: HearingState, user_input: UserInput) -> HearingTurn:
        return self._turn(
            state,
            "このヒアリングは完了しています。修正したい時は新しくヒアリングを始めてください！",
            done=True,
        )

    # --- 内部ヘルパ ---

    def _commit_current_habit(self, state: HearingState) -> None:
        assert state.current_habit is not None
        state.habits.append(state.current_habit)
        state.current_habit = None
        state.step = HearingStep.MORE_HABITS

    def _more_habits_turn(self, state: HearingState, prefix: str) -> HearingTurn:
        message = f"{prefix}他に何か悪習慣はありますか？".lstrip()
        return self._turn(
            state, message, choices=self._more_habits_choices(state), input_mode="free_text"
        )

    def _habit_recommendations(self, state: HearingState) -> list[Choice]:
        """登録済みラベルと重複しないレコメンドを返す"""
        used = {habit.label for habit in state.habits}
        return [c for c in HABIT_RECOMMENDATIONS if c.label not in used]

    def _more_habits_choices(self, state: HearingState) -> list[Choice]:
        return [*self._habit_recommendations(state), DONE_CHOICE]

    def _resolve_habit_text(self, user_input: UserInput) -> str:
        """自由入力またはレコメンド選択を悪習慣テキストに解決する"""
        if user_input.choice_id:
            rec = next(
                (c for c in HABIT_RECOMMENDATIONS if c.choice_id == user_input.choice_id), None
            )
            if rec is not None:
                return rec.label
        return (user_input.text or "").strip()

    async def _save_config(self, state: HearingState) -> MonitoringConfig:
        habits = [
            Habit(
                habit_id=f"habit_{i + 1}",
                label=draft.label,
                visual_cues=draft.visual_cues,
                judge_hint=draft.judge_hint,
                notification=draft.notification,
            )
            for i, draft in enumerate(state.habits)
            if draft.notification is not None
        ]
        config = MonitoringConfig(
            config_id=uuid.uuid4().hex,
            goal=state.goal or "",
            habits=habits,
            created_at=datetime.now(UTC),
        )
        await self._configs.save(config)
        return config

    def _config_summary(self, config: MonitoringConfig) -> str:
        lines = [f"目標: {config.goal}"]
        for habit in config.habits:
            if habit.notification.method == "bgm":
                track = get_bgm_track(habit.notification.bgm_track_id or "")
                notify = f"BGM ({track.label if track else '不明'})"
            else:
                notify = f"言葉 (「{habit.notification.phrase}」)"
            lines.append(f"・{habit.label} → {notify}")
        return "\n".join(lines)

    def _turn(
        self,
        state: HearingState,
        message: str,
        choices: list[Choice] | None = None,
        input_mode: str = "free_text",
        done: bool = False,
        config_id: str | None = None,
    ) -> HearingTurn:
        return HearingTurn(
            hearing_id=state.hearing_id,
            bot_message=message,
            input_mode=input_mode,  # type: ignore[arg-type]
            choices=choices,
            done=done,
            config_id=config_id,
        )
