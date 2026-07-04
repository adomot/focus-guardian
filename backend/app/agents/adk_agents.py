"""ADK LlmAgent の単発実行による構造化出力エージェント。

設計判断 (research.md 参照):
- output_schema 専用・tools なし・毎回新規 InMemory セッションの単発実行
- ADK セッション永続化には依存しない (Cloud Run のステートレス性対策)
- output_schema が無視される既知の報告があるため instruction にも JSON 形式を明記し、
  応答は必ず Pydantic でバリデーションする (逸脱は AgentError)
"""

import logging

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel, Field, ValidationError

from app.agents.base import AgentError
from app.models.config import DetectionCondition, MonitoringConfig
from app.models.monitoring import Frame, JudgmentResult, JudgmentState

logger = logging.getLogger(__name__)

APP_NAME = "focus-guardian"


async def run_single_shot(agent: LlmAgent, parts: list[types.Part]) -> str:
    """LlmAgent を新規 InMemory セッションで1回だけ実行し、最終応答テキストを返す"""
    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
    user_id = "single-shot"
    session = await session_service.create_session(app_name=APP_NAME, user_id=user_id)
    content = types.Content(role="user", parts=parts)

    final_text: str | None = None
    try:
        async for event in runner.run_async(
            user_id=user_id, session_id=session.id, new_message=content
        ):
            if event.is_final_response() and event.content and event.content.parts:
                text_parts = [p.text for p in event.content.parts if p.text]
                if text_parts:
                    final_text = "".join(text_parts)
    except Exception as exc:  # ADK/Gemini 由来の失敗は AgentError に正規化する
        raise AgentError(f"agent execution failed: {exc}") from exc

    if not final_text:
        raise AgentError("agent returned no final response")
    return final_text


def _parse_json(model_cls: type[BaseModel], text: str) -> BaseModel:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.removeprefix("json").strip()
    try:
        return model_cls.model_validate_json(cleaned)
    except ValidationError as exc:
        raise AgentError(f"schema validation failed: {exc}") from exc


STRUCTURING_INSTRUCTION = """\
あなたは監視AIエージェントの設定アシスタントです。
ユーザが自由に記述した「悪習慣」を、Webカメラの静止画像から判定できる検知条件に構造化してください。

必ず次の JSON 形式のみで応答してください (説明文・コードフェンス不要):
{"habit_label": "悪習慣の短い名前", "visual_cues": ["画像上の視覚的手がかり1", "手がかり2"], "judge_hint": "判定者向けの一文"}

- visual_cues は静止画1枚で確認できる具体的な視覚的特徴を1〜3個 (姿勢・持ち物・視線・目の開閉など)
- 画像から判定できない悪習慣 (例: 心の中の雑念) の場合も、最も近い観察可能な行動に落とし込む
- すべて日本語で書く

例: 入力「スマホをいじってしまう」
{"habit_label": "スマホいじり", "visual_cues": ["手にスマートフォンを持っている", "視線が机上や手元の端末に向いている"], "judge_hint": "人物がスマートフォンを操作しているか"}
"""


class AdkStructuringAgent:
    def __init__(self, model: str) -> None:
        self._agent = LlmAgent(
            name="structuring_agent",
            model=model,
            description="悪習慣を画像判定可能な検知条件に構造化する",
            instruction=STRUCTURING_INSTRUCTION,
            output_schema=DetectionCondition,
        )

    async def structure_habit(self, raw_text: str) -> DetectionCondition:
        text = await run_single_shot(
            self._agent, [types.Part.from_text(text=f"悪習慣: {raw_text}")]
        )
        condition = _parse_json(DetectionCondition, text)
        assert isinstance(condition, DetectionCondition)
        return condition


class JudgeOutput(BaseModel):
    """JudgeAgent の出力スキーマ (habit_id の妥当性は呼び出し側で検証)"""

    state: JudgmentState
    habit_id: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


JUDGE_INSTRUCTION_TEMPLATE = """\
あなたは集中支援AIエージェントの判定担当です。
Webカメラの静止画1枚から、作業者の現在の状態を分類してください。

## 監視対象の悪習慣
{habit_lines}

## 分類ルール
- 上記の悪習慣に該当する視覚的手がかりが確認できる場合: state="habit"、該当する habit_id を設定
- 人物が写っていない・画角外の場合: state="absent" (habit_id は null)
- どの悪習慣にも該当しない場合: state="focused" (habit_id は null)。迷ったら focused を選ぶ
- confidence は判定の確信度 (0.0〜1.0)。画像が不鮮明・判断材料が乏しい場合は低くする

## 判定例
例1: 人物が机に向かいノートに書き物をしている → {{"state": "focused", "habit_id": null, "confidence": 0.9, "reason": "机に向かって書き物をしており作業に集中している"}}
例2: 人物が手にスマートフォンを持ち画面を見ている (habit_1=スマホいじり) → {{"state": "habit", "habit_id": "habit_1", "confidence": 0.85, "reason": "スマートフォンを手に持ち画面を注視している"}}
例3: 椅子に誰も座っていない → {{"state": "absent", "habit_id": null, "confidence": 0.95, "reason": "人物が画角内に写っていない"}}

必ず次の JSON 形式のみで応答してください (説明文・コードフェンス不要):
{{"state": "focused|habit|absent", "habit_id": "該当IDまたはnull", "confidence": 0.0, "reason": "日本語一文"}}
"""


def build_judge_instruction(config: MonitoringConfig) -> str:
    habit_lines = "\n".join(
        f"- habit_id={h.habit_id} 「{h.label}」: {h.judge_hint} (手がかり: {', '.join(h.visual_cues)})"
        for h in config.habits
    )
    return JUDGE_INSTRUCTION_TEMPLATE.format(habit_lines=habit_lines)


class AdkJudgeAgent:
    def __init__(self, model: str) -> None:
        self._model = model

    async def judge(self, frame: Frame, config: MonitoringConfig) -> JudgmentResult:
        agent = LlmAgent(
            name="judge_agent",
            model=self._model,
            description="画像から作業者の状態を分類する",
            instruction=build_judge_instruction(config),
            output_schema=JudgeOutput,
        )
        parts = [
            types.Part.from_bytes(data=frame.jpeg_bytes, mime_type="image/jpeg"),
            types.Part.from_text(text="この画像の作業者の状態を分類してください。"),
        ]
        text = await run_single_shot(agent, parts)
        output = _parse_json(JudgeOutput, text)
        assert isinstance(output, JudgeOutput)

        habit_id = output.habit_id
        if output.state == JudgmentState.HABIT:
            valid_ids = {h.habit_id for h in config.habits}
            if habit_id not in valid_ids:
                raise AgentError(f"judge returned unknown habit_id: {habit_id}")
        else:
            habit_id = None
        return JudgmentResult(
            state=output.state,
            habit_id=habit_id,
            confidence=output.confidence,
            reason=output.reason,
        )
