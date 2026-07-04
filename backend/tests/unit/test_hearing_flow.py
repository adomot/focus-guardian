"""固定フローヒアリングの全遷移テスト (要件 1.1〜1.10)"""

import pytest

from app.agents.base import AgentError
from app.models.hearing import UserInput
from app.repositories.memory import MemoryHearingRepository
from app.services.hearing_flow import HearingFlowService, HearingNotFoundError
from app.services.speech_assets import FakeSpeechAssetService
from tests.conftest import choice, run_default_hearing, text


async def test_full_flow_matches_conversation_example(hearing_flow, config_repo):
    """要件の会話例どおりの完走 (1.1〜1.7)"""
    turn = await hearing_flow.start()
    assert "実現したい目標" in turn.bot_message
    assert turn.input_mode == "free_text"
    hid = turn.hearing_id

    turn = await hearing_flow.reply(hid, text("美容検定1級が欲しい！"))
    assert "悪習慣" in turn.bot_message

    turn = await hearing_flow.reply(hid, text("スマホをいじってしまう。"))
    assert "どのような通知" in turn.bot_message
    assert turn.input_mode == "choices"
    assert {c.choice_id for c in turn.choices} == {"bgm", "speech"}

    turn = await hearing_flow.reply(hid, choice("bgm"))
    assert "どのBGM" in turn.bot_message
    assert turn.input_mode == "choices"

    turn = await hearing_flow.reply(hid, choice("focus"))
    assert "他に何か悪習慣" in turn.bot_message
    assert any(c.choice_id == "done" for c in turn.choices)

    turn = await hearing_flow.reply(hid, text("居眠りをしてしまう。"))
    assert "どのような通知" in turn.bot_message

    turn = await hearing_flow.reply(hid, choice("speech"))
    assert "どのような言葉" in turn.bot_message
    assert turn.input_mode == "free_text"

    turn = await hearing_flow.reply(hid, text("起きてください"))
    assert "他に何か悪習慣" in turn.bot_message

    turn = await hearing_flow.reply(hid, choice("done"))
    assert turn.done is True
    assert "ありがとうございました" in turn.bot_message
    assert turn.config_id

    config = await config_repo.get(turn.config_id)
    assert config is not None
    assert config.goal == "美容検定1級が欲しい！"
    assert len(config.habits) == 2
    assert config.habits[0].notification.method == "bgm"
    assert config.habits[0].notification.bgm_track_id == "focus"
    assert config.habits[1].notification.method == "speech"
    assert config.habits[1].notification.phrase == "起きてください"
    # 設定要約の確認提示 (1.5)
    assert "起きてください" in turn.bot_message


async def test_unexpected_input_represents_same_question(hearing_flow):
    """想定外入力では状態を変えず同一質問を再提示する (1.10)"""
    turn = await hearing_flow.start()
    hid = turn.hearing_id

    # GOAL ステップに空入力
    turn = await hearing_flow.reply(hid, UserInput())
    assert "実現したい目標" in turn.bot_message

    await hearing_flow.reply(hid, text("目標"))
    await hearing_flow.reply(hid, text("スマホ"))

    # NOTIFY_TYPE (choices) に自由入力
    turn = await hearing_flow.reply(hid, text("なんか適当な入力"))
    assert "どのような通知" in turn.bot_message

    # 不正な choice_id
    turn = await hearing_flow.reply(hid, choice("invalid"))
    assert "どのような通知" in turn.bot_message

    # BGM_SELECT に不正な track
    await hearing_flow.reply(hid, choice("bgm"))
    turn = await hearing_flow.reply(hid, choice("no-such-track"))
    assert "どのBGM" in turn.bot_message


async def test_structuring_failure_reprompts(config_repo):
    """構造化失敗時は同一質問を再提示する (1.8 エラー経路)"""

    class FailingStructuringAgent:
        async def structure_habit(self, raw_text: str):
            raise AgentError("boom")

    flow = HearingFlowService(
        hearings=MemoryHearingRepository(),
        configs=config_repo,
        structuring=FailingStructuringAgent(),
        assets=FakeSpeechAssetService(),
    )
    turn = await flow.start()
    hid = turn.hearing_id
    await flow.reply(hid, text("目標"))
    turn = await flow.reply(hid, text("スマホをいじってしまう"))
    assert "悪習慣" in turn.bot_message  # HABIT ステップに留まる
    assert "うまく理解できませんでした" in turn.bot_message


async def test_unknown_hearing_id_raises(hearing_flow):
    with pytest.raises(HearingNotFoundError):
        await hearing_flow.reply("no-such-id", text("x"))


async def test_completed_hearing_stays_done(hearing_flow):
    config_id = await run_default_hearing(hearing_flow)
    assert config_id
    # DONE 後の追加入力
    state_turn = await hearing_flow.start()
    turn = await hearing_flow.reply(state_turn.hearing_id, text("目標"))
    assert "悪習慣" in turn.bot_message
