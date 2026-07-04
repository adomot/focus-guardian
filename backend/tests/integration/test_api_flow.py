"""ヒアリング → セッション → 判定 → 介入 → サマリーの縦串統合テスト (タスク 7.1)"""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

JPEG_MAGIC = b"\xff\xd8\xff"


@pytest.fixture
def client() -> TestClient:
    settings = Settings(
        repository_backend="memory",
        agents_backend="fake",
        assets_backend="fake",
        speaker_adapter="null",
        frame_rate_limit_per_minute=1000,
        _env_file=None,
    )
    app = create_app(settings)
    return TestClient(app, raise_server_exceptions=False)


def frame(marker: bytes = b"") -> bytes:
    return JPEG_MAGIC + marker + b"\x00" * 32


def post_frame(client: TestClient, session_id: str, marker: bytes = b""):
    return client.post(
        f"/api/sessions/{session_id}/frames",
        files={"image": ("f.jpg", frame(marker), "image/jpeg")},
    )


def complete_hearing(client: TestClient) -> str:
    turn = client.post("/api/hearing").json()
    hid = turn["hearing_id"]

    def reply(body: dict) -> dict:
        res = client.post(f"/api/hearing/{hid}/reply", json=body)
        assert res.status_code == 200
        return res.json()

    reply({"text": "美容検定1級が欲しい！"})
    reply({"text": "スマホをいじってしまう。"})
    reply({"choice_id": "bgm"})
    reply({"choice_id": "focus"})
    reply({"text": "居眠りをしてしまう。"})
    reply({"choice_id": "speech"})
    turn = reply({"text": "起きてください"})
    turn = reply({"choice_id": "done"})
    assert turn["done"] is True
    return turn["config_id"]


def test_full_vertical_flow(client: TestClient):
    config_id = complete_hearing(client)

    latest = client.get("/api/configs/latest").json()
    assert latest["config_id"] == config_id

    session = client.post("/api/sessions", json={"config_id": config_id}).json()
    sid = session["session_id"]
    assert session["status"] == "active"

    # 集中 → 介入なし
    result = post_frame(client, sid).json()
    assert result["judgment"]["state"] == "focused"
    assert result["intervention"] is None

    # 悪習慣 1回目 → まだ発火しない
    result = post_frame(client, sid, b"HABIT:habit_1:").json()
    assert result["judgment"]["state"] == "habit"
    assert result["intervention"] is None

    # 悪習慣 2回目 → 発火。NullSpeaker なのでブラウザフォールバック (4.8)
    result = post_frame(client, sid, b"HABIT:habit_1:").json()
    assert result["intervention"] is not None
    assert result["intervention"]["delivered_by"] == "browser"
    assert result["intervention"]["method"] == "bgm"
    intervention_id = result["intervention"]["intervention_id"]

    # 復帰 → 介入結果が returned に更新される (5.1, 5.2)
    result = post_frame(client, sid).json()
    assert result["intervention"] is None

    # セッション終了とサマリー (6.3)
    summary = client.post(f"/api/sessions/{sid}/end").json()
    assert summary["frames"] == 4
    assert summary["interventions"] == 1
    assert summary["returned_count"] == 1
    assert summary["habit_detected"] == 2
    assert summary["goal"] == "美容検定1級が欲しい！"
    assert intervention_id

    # 終了済みセッションへのフレームは 409
    res = post_frame(client, sid)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "session_ended"


def test_frame_validation(client: TestClient):
    config_id = complete_hearing(client)
    sid = client.post("/api/sessions", json={"config_id": config_id}).json()["session_id"]

    # 非 JPEG は 400
    res = client.post(
        f"/api/sessions/{sid}/frames", files={"image": ("f.png", b"PNGDATA", "image/png")}
    )
    assert res.status_code == 400

    # 存在しないセッションは 404
    res = client.post(
        "/api/sessions/nonexistent/frames",
        files={"image": ("f.jpg", frame(), "image/jpeg")},
    )
    assert res.status_code == 404


def test_session_without_config_is_404(client: TestClient):
    res = client.post("/api/sessions", json={})
    assert res.status_code == 404


def test_judge_error_is_recorded_and_loop_continues(client: TestClient):
    """Gemini 失敗経路: エラー記録のみで 200、次周期で継続 (3.5)"""
    config_id = complete_hearing(client)
    sid = client.post("/api/sessions", json={"config_id": config_id}).json()["session_id"]

    # FakeJudgeAgent は不明な habit_id マーカーでも動くため、エージェント差し替えで再現
    from app.agents.base import AgentError

    class BoomJudge:
        async def judge(self, frame, config):
            raise AgentError("gemini down")

    container = client.app.state.container
    container.monitoring._judge = BoomJudge()

    result = post_frame(client, sid)
    assert result.status_code == 200
    assert result.json()["judgment"]["state"] == "error"
    assert result.json()["intervention"] is None
