# log-lite

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Structured logging setup in one call: JSON or plain output, console + file handlers, bound context fields, and config validation that fails fast on typos.

## 🚀 Overview

Python's `logging` is powerful and famously fiddly. `log-lite` wraps it with a frozen `LogConfig` dataclass — validate your options at construction, add console/file/JSON handlers in one `setup_logging()` call, then bind context (tenant, request_id) to loggers that flows into every line without touching call sites.

## ✨ Features

- **Frozen config:** `LogConfig(level=..., json_mode=True, file_path=...)` — invalid levels and unknown keys raise immediately
- **One-call setup:** console, file handler, or both; idempotent unless `force=True`
- **JSON mode:** every line a parseable object with ts/level/logger/message + extras + shared context
- **Bound context:** `log.bind(request_id="r1")` returns a child logger carrying fields forward
- **Extra-field pass-through:** `log.info("msg", path="/x")` attaches structured fields
- **NullHandler fallback:** silent-safe when no outputs configured
- **Zero dependencies**

## 🚧 Structure

```
logging-framework-lite/
├── src/log_lite/
│   ├── __init__.py
│   └── core.py
├── tests/
│   └── test_core.py
├── README.md
└── pyproject.toml
```

## 📦 Installation

### For Development

```bash
git clone https://github.com/supremeloki/logging-framework-lite.git
cd logging-framework-lite
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## 📋 Requirements

- Python 3.11+
- No runtime dependencies

## 🏃 Quick Start

```python
from pathlib import Path
from log_lite import LogConfig, setup_logging, get_logger

config = LogConfig(
    level="INFO",
    json_mode=True,
    file_path=Path("logs/app.log"),
)
setup_logging(config)

log = get_logger("svc.orders", service="orders")
log.info("order received", order_id=42)
```

Each line in `app.log`:

```json
{"ts": "2026-08-24T18:00:00+00:00", "level": "INFO", "logger": "svc.orders", "message": "order received", "service": "orders", "order_id": 42}
```

### Bound children

```python
request_log = log.bind(request_id="r-9")
request_log.warning("slow query", ms=830)
```

## 🔧 Error Handling

```text
LoggingSetupError   # unknown level, unknown config key
```

Logging itself never raises after setup — bad calls are stdlib behavior.

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📝 Code Quality

- Full type hints (`X | None` style), frozen `LogConfig`
- Zero comments — names carry the meaning
- `ruff` clean

## 📄 License

MIT — see [LICENSE](LICENSE).

## 👤 Author

**Kooroush Masoumi**

---

⭐ Star this repo if you find it useful!
