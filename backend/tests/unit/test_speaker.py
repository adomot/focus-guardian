"""スピーカーアダプタのテスト (要件 4.7, 4.9)"""

import httpx

from app.adapters.speaker import NullSpeaker, VoiceMonkeySpeaker


async def test_null_speaker_always_fails_to_browser_fallback():
    result = await NullSpeaker().play("https://a/x.mp3")
    assert result.ok is False


async def test_voicemonkey_missing_config():
    speaker = VoiceMonkeySpeaker(base_url="https://vm", token="", device="")
    result = await speaker.play("https://a/x.mp3")
    assert result.ok is False
    assert result.error == "config"


def make_speaker(handler) -> VoiceMonkeySpeaker:
    return VoiceMonkeySpeaker(
        base_url="https://api-v3.voicemonkey.io",
        token="tok",
        device="dev",
        transport=httpx.MockTransport(handler),
    )


async def test_voicemonkey_success():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("authorization")
        captured["url"] = str(request.url)
        return httpx.Response(200, json={"success": True})

    result = await make_speaker(handler).play("https://a/x.mp3")
    assert result.ok is True
    assert captured["auth"] == "Bearer tok"
    assert captured["url"].endswith("/announce")


async def test_voicemonkey_throttled_retries_once_then_fails(monkeypatch):
    monkeypatch.setattr(VoiceMonkeySpeaker, "RETRY_DELAY_SECONDS", 0.0)
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(429, text="THROTTLED:123")

    result = await make_speaker(handler).play("https://a/x.mp3")
    assert result.ok is False
    assert result.error == "throttled"
    assert calls["n"] == 2


async def test_voicemonkey_quota_exceeded_no_retry():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(429, text="MONTHLY_QUOTA_EXCEEDED")

    result = await make_speaker(handler).play("https://a/x.mp3")
    assert result.error == "quota_exceeded"
    assert calls["n"] == 1


async def test_voicemonkey_network_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    result = await make_speaker(handler).play("https://a/x.mp3")
    assert result.ok is False
    assert result.error == "unreachable"
