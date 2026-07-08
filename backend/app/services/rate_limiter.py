"""Gemini 呼び出しのグローバル日次上限。

コスト暴走の最終防波堤。フレーム API のセッション単位レート制限とは別に、
アプリ全体で 1 日あたりの Gemini 呼び出し総数を上限で打ち止める。
日付境界は JST (UTC+9 固定、日本は DST なし) で判定する。
"""

from datetime import UTC, datetime, timedelta
from typing import Protocol

JST = timedelta(hours=9)


def day_key(now: datetime) -> str:
    """UTC の now を JST の日付キー (gemini-YYYY-MM-DD) に変換する"""
    jst = now.astimezone(UTC) + JST
    return f"gemini-{jst:%Y-%m-%d}"


class GlobalRateLimiter(Protocol):
    async def try_consume(self, now: datetime) -> bool:
        """呼び出しを 1 つ消費できたら True。上限到達なら False (消費しない)。"""
        ...


class MemoryDailyRateLimiter:
    """ローカル/テスト用。プロセス内カウンタ (再起動で消える)。"""

    def __init__(self, limit: int) -> None:
        self._limit = limit
        self._counts: dict[str, int] = {}

    async def try_consume(self, now: datetime) -> bool:
        key = day_key(now)
        current = self._counts.get(key, 0)
        if current >= self._limit:
            return False
        self._counts[key] = current + 1
        return True


class FirestoreDailyRateLimiter:
    """本番用。日付キーのドキュメントをトランザクションで原子的に増分する。

    Cloud Run の再起動・スケールアウトでもカウンタが保持される。
    """

    COLLECTION = "rate_limits"

    def __init__(self, client, limit: int) -> None:
        self._db = client
        self._limit = limit

    async def try_consume(self, now: datetime) -> bool:
        from google.cloud import firestore

        doc_ref = self._db.collection(self.COLLECTION).document(day_key(now))
        transaction = self._db.transaction()
        limit = self._limit

        @firestore.async_transactional
        async def _run(tx: firestore.AsyncTransaction) -> bool:
            snap = await doc_ref.get(transaction=tx)
            current = snap.to_dict().get("count", 0) if snap.exists else 0
            if current >= limit:
                return False
            tx.set(doc_ref, {"count": current + 1}, merge=True)
            return True

        return await _run(transaction)
