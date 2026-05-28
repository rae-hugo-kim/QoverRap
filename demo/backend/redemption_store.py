"""SQLite-backed one-time-use redemption counter for QoverwRap demo.

The signature (Layer C hex) is used as the primary key because:
  - Ed25519 is deterministic: identical inputs produce identical signatures.
  - A cloned QR (bit-for-bit copy) shares the same signature → same key → detected.
  - A forged QR (different or absent signature) is rejected before reaching the store.

DB path resolution order:
  1. Explicit ``conn`` argument (used by tests for :memory: isolation).
  2. Environment variable ``QWR_REDEMPTION_DB``.
  3. Default ``demo/backend/redemptions.db`` relative to this file.
"""
from __future__ import annotations

import os
import sqlite3
import threading
from pathlib import Path
from typing import Optional

_DEFAULT_DB = Path(__file__).parent / "redemptions.db"

_DDL = """
CREATE TABLE IF NOT EXISTS redemptions (
    signature  TEXT    PRIMARY KEY,
    use_count  INTEGER NOT NULL DEFAULT 0,
    max_uses   INTEGER NOT NULL DEFAULT 1,
    first_seen TEXT    NOT NULL DEFAULT (datetime('now')),
    last_seen  TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


class RedemptionStore:
    """Thread-safe SQLite wrapper for the redemption counter table."""

    def __init__(self, conn: Optional[sqlite3.Connection] = None) -> None:
        if conn is not None:
            self._conn = conn
        else:
            db_path = os.environ.get("QWR_REDEMPTION_DB", str(_DEFAULT_DB))
            self._conn = sqlite3.connect(db_path, check_same_thread=False)
        # Autocommit mode: we manage transactions explicitly via BEGIN IMMEDIATE.
        self._conn.isolation_level = None
        self._conn.execute(_DDL)
        # Serializes redeem() across threads that share this connection — SQLite
        # forbids nested transactions on a single connection, so we cannot rely
        # on BEGIN IMMEDIATE alone when check_same_thread=False is in effect.
        self._lock = threading.Lock()

    def redeem(self, signature_hex: str, max_uses: int) -> tuple[str, int]:
        """Attempt to redeem one use slot for the given signature.

        Returns (status, use_count) where status is one of:
          "ok"           – slot consumed; use_count is the *new* value.
          "already_used" – max_uses already reached; use_count is unchanged.
        """
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "SELECT use_count, max_uses FROM redemptions WHERE signature = ?",
                    (signature_hex,),
                )
                row = cur.fetchone()

                if row is None:
                    if max_uses < 1:
                        self._conn.execute("ROLLBACK")
                        return ("already_used", 0)
                    self._conn.execute(
                        """
                        INSERT INTO redemptions (signature, use_count, max_uses)
                        VALUES (?, 1, ?)
                        """,
                        (signature_hex, max_uses),
                    )
                    self._conn.execute("COMMIT")
                    return ("ok", 1)

                current_count, stored_max = row
                effective_max = stored_max

                if current_count >= effective_max:
                    self._conn.execute("ROLLBACK")
                    return ("already_used", current_count)

                new_count = current_count + 1
                self._conn.execute(
                    """
                    UPDATE redemptions
                    SET use_count = ?, last_seen = datetime('now')
                    WHERE signature = ?
                    """,
                    (new_count, signature_hex),
                )
                self._conn.execute("COMMIT")
                return ("ok", new_count)
            except Exception:
                self._conn.execute("ROLLBACK")
                raise
