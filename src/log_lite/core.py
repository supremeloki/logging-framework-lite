from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_FORMAT = "%(asctime)s %(levelname)-7s %(name)s :: %(message)s"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


class LoggingSetupError(Exception):
    pass


@dataclass(frozen=True)
class LogConfig:
    level: str = "INFO"
    format: str = DEFAULT_FORMAT
    date_format: str = DATE_FORMAT
    console: bool = True
    file_path: Path | None = None
    json_mode: bool = False
    context: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise LoggingSetupError(f"unknown level: {self.level!r}")


class JsonFormatter(logging.Formatter):
    def __init__(self, context: dict[str, Any] | None = None) -> None:
        super().__init__()
        self._context = context or {}

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in logging.LogRecord("x", 0, "", 0, (), None, None).__dict__
            and key not in {"message", "asctime"}
        }
        entry.update(self._context)
        entry.update(extra_fields)
        return json.dumps(entry, ensure_ascii=False, default=str)


def build_config(**overrides: Any) -> LogConfig:
    known = {f.name for f in LogConfig.__dataclass_fields__.values()}
    unknown = set(overrides) - known
    if unknown:
        raise LoggingSetupError(f"unknown config keys: {sorted(unknown)}")
    return LogConfig(**overrides)


def setup_logging(config: LogConfig | None = None, force: bool = False) -> logging.Logger:
    active = config or LogConfig()
    root = logging.getLogger()
    if root.handlers and not force:
        return root
    if force:
        for handler in list(root.handlers):
            root.removeHandler(handler)
    root.setLevel(active.level)
    formatter: logging.Formatter
    if active.json_mode:
        formatter = JsonFormatter(context=dict(active.context))
    else:
        formatter = logging.Formatter(active.format, datefmt=active.date_format)
    if active.console:
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)
    if active.file_path is not None:
        active.file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(active.file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    if not root.handlers:
        null_handler = logging.NullHandler()
        root.addHandler(null_handler)
    return root


def get_logger(name: str, **bound_context: Any) -> BoundLogger:
    return BoundLogger(logging.LoggerAdapter(logging.getLogger(name), dict(bound_context)))


class BoundLogger:
    def __init__(self, base: logging.Logger | logging.LoggerAdapter[logging.Logger]) -> None:
        self._base = base

    @property
    def logger(self) -> logging.Logger:
        if isinstance(self._base, logging.LoggerAdapter):
            return self._base.logger
        return self._base

    @property
    def extra(self) -> dict[str, Any]:
        if isinstance(self._base, logging.LoggerAdapter):
            return dict(self._base.extra)
        return {}

    def bind(self, **extra: Any) -> "BoundLogger":
        merged = {**self.extra, **extra}
        return BoundLogger(logging.LoggerAdapter(self.logger, merged))

    def debug(self, message: str, /, **kw: Any) -> None:
        self.logger.debug(message, extra=kw)

    def info(self, message: str, /, **kw: Any) -> None:
        self.logger.info(message, extra=kw)

    def warning(self, message: str, /, **kw: Any) -> None:
        self.logger.warning(message, extra=kw)

    def error(self, message: str, /, exc_info: bool = False, **kw: Any) -> None:
        self.logger.error(message, exc_info=exc_info, extra=kw)
