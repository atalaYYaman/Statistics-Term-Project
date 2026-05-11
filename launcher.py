from __future__ import annotations

# PyInstaller paketi için çalışma dizini ve sys.path ayarı; ardından Streamlit ile app.py çalıştırılır.

import os
import sys
from pathlib import Path

from streamlit.web import cli as stcli


def _base_dir() -> Path:
    # Paketlenmiş çalışmada kök _MEIPASS; geliştirmede bu dosyanın bulunduğu klasör.
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def main() -> None:
    # Masaüstü kullanımı için localhost adresi ve port sabitlenir.
    base_dir = _base_dir()
    app_path = base_dir / "app.py"
    os.chdir(base_dir)
    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))
    # Yerel Streamlit adresinin öngörülebilir olması için ortam değişkenleri.
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "false")
    os.environ.setdefault("STREAMLIT_SERVER_ADDRESS", "localhost")
    os.environ.setdefault("STREAMLIT_SERVER_PORT", "8501")
    os.environ.setdefault("STREAMLIT_BROWSER_SERVER_ADDRESS", "localhost")
    os.environ.setdefault("STREAMLIT_GLOBAL_DEVELOPMENT_MODE", "false")
    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--global.developmentMode=false",
        "--server.address=localhost",
        "--server.port=8501",
        "--server.headless=false",
        "--browser.serverAddress=localhost",
    ]
    raise SystemExit(stcli.main())


if __name__ == "__main__":
    main()
