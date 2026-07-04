"""タスク 1.2 実機スパイク: ADK+Vertex Gemini / Cloud TTS の縦串検証 (一時スクリプト)"""

import asyncio
import sys
from datetime import UTC, datetime

from app.agents.adk_agents import AdkJudgeAgent, AdkStructuringAgent
from app.models.config import Habit, MonitoringConfig, Notification
from app.models.monitoring import Frame
from app.services.speech_assets import GcsSpeechAssetService


async def main(image_path: str, bucket: str) -> None:
    print("=== 1) StructuringAgent (ADK + Vertex Gemini) ===")
    structuring = AdkStructuringAgent("gemini-2.5-flash-lite")
    condition = await structuring.structure_habit("スマホをいじってしまう")
    print(condition.model_dump_json(indent=2))

    print("=== 2) JudgeAgent (画像判定) ===")
    config = MonitoringConfig(
        config_id="spike",
        goal="spike",
        habits=[
            Habit(
                habit_id="habit_1",
                label=condition.habit_label,
                visual_cues=condition.visual_cues,
                judge_hint=condition.judge_hint,
                notification=Notification(
                    method="bgm", bgm_track_id="focus", audio_url="https://example.com/x.mp3"
                ),
            )
        ],
        created_at=datetime.now(UTC),
    )
    judge = AdkJudgeAgent("gemini-2.5-flash-lite")
    with open(image_path, "rb") as f:
        frame = Frame(jpeg_bytes=f.read(), captured_at=datetime.now(UTC))
    result = await judge.judge(frame, config)
    print(result.model_dump_json(indent=2))

    print("=== 3) Cloud TTS 日本語 → GCS ===")
    assets = GcsSpeechAssetService(bucket)
    url = await assets.synthesize_phrase("起きてください。作業に戻りましょう。")
    print(f"generated: {url}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2]))
