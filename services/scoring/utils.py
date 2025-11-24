from __future__ import annotations

import hashlib


def deterministic_score(seed_input: str, offset: int) -> float:
    """生成稳定可复现的 0~1 之间评分，用于模拟真实模型输出。"""
    payload = f"{seed_input}:{offset}".encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    integer = int(digest[:8], 16)
    return round((integer % 1000) / 1000, 3)
