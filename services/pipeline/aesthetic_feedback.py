from __future__ import annotations

import asyncio
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .prompt_bank_cn import _resolve_path

logger = logging.getLogger(__name__)


class AestheticFeedback:
    """模板权重反馈模块，基于美学分数异步更新 Prompt Bank。"""

    def __init__(
        self,
        bank_path: str = "prompt_bank_cn.json",
        log_path: str = "logs/prompt_bank_update.log",
        alpha: float = 0.8,
    ) -> None:
        self.bank_path = _resolve_path(bank_path)
        self.log_path = _resolve_path(log_path) if not Path(log_path).is_absolute() else Path(log_path)
        self.alpha = max(0.0, min(1.0, alpha))
        self._lock = threading.Lock()
        self._ensure_log_folder()

    def _ensure_log_folder(self) -> None:
        log_dir = self.log_path.parent
        log_dir.mkdir(parents=True, exist_ok=True)

    async def update(self, template_id: Optional[str], aesthetic_score: Optional[float]) -> None:
        """异步更新模板权重，主流程中调用时无需 await。"""
        if not template_id:
            logger.debug("模板 ID 为空，跳过权重更新。")
            return
        normalized = self._normalize_score(aesthetic_score)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._update_sync, template_id, normalized)

    def _update_sync(self, template_id: str, score: float) -> None:
        try:
            with self._lock:
                bank = self._load_bank()
                updated = False
                for entry in bank:
                    if entry.get("id") == template_id:
                        old_weight = float(entry.get("权重") or 0.5)
                        new_weight = self.alpha * old_weight + (1 - self.alpha) * score
                        entry["权重"] = round(float(new_weight), 6)
                        updated = True
                        self._append_log(template_id, old_weight, entry["权重"], score)
                        break
                if updated:
                    self._save_bank(bank)
                else:
                    logger.warning("在 PromptBank 中未找到模板 %s", template_id)
        except Exception as exc:  # pragma: no cover - 保护日志写入
            logger.exception("更新模板权重失败: %s", exc)

    def _load_bank(self) -> list[Dict[str, Any]]:
        if not self.bank_path.exists():
            raise FileNotFoundError(f"Prompt bank 文件不存在: {self.bank_path}")
        with self.bank_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, list):
            raise ValueError("Prompt bank 数据格式错误，应为数组。")
        return data

    def _save_bank(self, data: list[Dict[str, Any]]) -> None:
        tmp_path = self.bank_path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        tmp_path.replace(self.bank_path)

    def _append_log(self, template_id: str, old_weight: float, new_weight: float, score: float) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        line = (
            f"{timestamp}\ttemplate_id={template_id}\told={old_weight:.4f}"
            f"\tnew={new_weight:.4f}\tscore={score:.4f}\n"
        )
        with self.log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(line)

    @staticmethod
    def _normalize_score(score: Optional[float]) -> float:
        if score is None or not isinstance(score, (int, float)):
            return 0.5
        return max(0.0, min(1.0, float(score)))
