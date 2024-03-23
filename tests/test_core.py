import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from log_lite import (
    BoundLogger,
    LogConfig,
    LoggingSetupError,
    build_config,
    setup_logging,
)


@pytest.fixture(autouse=True)
def clean_root():
    root = logging.getLogger()
    saved = list(root.handlers)
    for handler in saved:
        root.removeHandler(handler)
    yield
    for handler in list(root.handlers):
        root.removeHandler(handler)
    for handler in saved:
        root.addHandler(handler)


def test_invalid_level_rejected():
    with pytest.raises(LoggingSetupError):
        build_config(level="LOUD")


def test_unknown_key_rejected():
    with pytest.raises(LoggingSetupError):
        build_config(colour="red")


def test_setup_adds_console_handler():
    logger = setup_logging(LogConfig(console=True), force=True)
    assert any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in logger.handlers)


def test_setup_writes_file(tmp_path: Path):
    target = tmp_path / "logs" / "app.log"
    setup_logging(LogConfig(console=False, file_path=target), force=True)
    logging.getLogger("probe").warning("hello file")
    for handler in logging.getLogger().handlers:
        handler.flush()
    assert target.exists()
    assert "hello file" in target.read_text(encoding="utf-8")


def test_json_output_is_parseable(tmp_path: Path):
    target = tmp_path / "j.log"
    config = LogConfig(console=False, file_path=target, json_mode=True, context={"app": "t"})
    setup_logging(config, force=True)
    logging.getLogger("probe.j").error("boom", extra={"request_id": "r-9"})
    for handler in logging.getLogger().handlers:
        handler.flush()
    line = target.read_text(encoding="utf-8").strip().splitlines()[0]
    parsed = json.loads(line)
    assert parsed["message"] == "boom"
    assert parsed["level"] == "ERROR"
    assert parsed["request_id"] == "r-9"
    assert parsed["app"] == "t"


def test_second_setup_without_force_is_noop():
    first = setup_logging(LogConfig(), force=True)
    count_before = len(first.handlers)
    second = setup_logging(LogConfig())
    assert len(second.handlers) == count_before


def test_bound_logger_merges_context():
    records: list[logging.LogRecord] = []
