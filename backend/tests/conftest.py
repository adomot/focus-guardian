import pytest

from app.agents.fake import FakeStructuringAgent
from app.models.hearing import UserInput
from app.repositories.memory import (
    MemoryConfigRepository,
    MemoryHearingRepository,
    MemorySessionRepository,
)
from app.services.hearing_flow import HearingFlowService
from app.services.speech_assets import FakeSpeechAssetService


@pytest.fixture
def config_repo() -> MemoryConfigRepository:
    return MemoryConfigRepository()


@pytest.fixture
def session_repo() -> MemorySessionRepository:
    return MemorySessionRepository()


@pytest.fixture
def hearing_flow(config_repo: MemoryConfigRepository) -> HearingFlowService:
    return HearingFlowService(
        hearings=MemoryHearingRepository(),
        configs=config_repo,
        structuring=FakeStructuringAgent(),
        assets=FakeSpeechAssetService(),
    )


def text(value: str) -> UserInput:
    return UserInput(text=value)


def choice(value: str) -> UserInput:
    return UserInput(choice_id=value)


async def run_default_hearing(hearing_flow: HearingFlowService) -> str:
    """会話例どおりにヒアリングを完走させ config_id を返すテストヘルパ"""
    turn = await hearing_flow.start()
    hid = turn.hearing_id
    await hearing_flow.reply(hid, text("美容検定1級が欲しい！"))
    await hearing_flow.reply(hid, text("スマホをいじってしまう。"))
    await hearing_flow.reply(hid, choice("bgm"))
    await hearing_flow.reply(hid, choice("focus"))
    await hearing_flow.reply(hid, text("居眠りをしてしまう。"))
    await hearing_flow.reply(hid, choice("speech"))
    await hearing_flow.reply(hid, text("起きてください"))
    turn = await hearing_flow.reply(hid, choice("done"))
    assert turn.done and turn.config_id
    return turn.config_id
