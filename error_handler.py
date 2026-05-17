"""Global error handling for ScreenChurch.

PyInstaller's --windowed build has no console attached. Without a custom
sys.excepthook, any unhandled exception terminates the process silently and
the operator only sees the window disappear. This module installs a hook that:

  - writes the full traceback to ScreenChurchData/logs/crash.log
  - shows a QMessageBox with the error so the operator can report it

It also exposes a thin `log_warning` helper so other modules can append
non-fatal events to the same log file.
"""

from __future__ import annotations

import datetime as _datetime
import os
import sys
import traceback


_LOG_FILENAME = "crash.log"


def _resolve_logs_dir() -> str:
    """Mirror DataStorageMixin.default_data_root, without needing the mixin.

    Used at startup before MainWindow exists. Kept intentionally simple: it
    must not raise, even if Documents/HOME is missing.
    """
    base = os.path.dirname(os.path.abspath(__file__))
    portable = os.path.join(base, "ScreenChurchData")
    if os.path.isdir(portable):
        root = portable
    else:
        env_root = os.environ.get("SCREENCHURCH_DATA_DIR")
        if env_root:
            root = env_root
        else:
            documents = os.path.join(os.path.expanduser("~"), "Documents")
            if not os.path.isdir(documents):
                documents = os.path.expanduser("~")
            root = os.path.join(documents, "ScreenChurchData")
    logs_dir = os.path.join(root, "logs")
    try:
        os.makedirs(logs_dir, exist_ok=True)
    except OSError:
        # Fall back to the program directory if the data root is unavailable.
        logs_dir = base
    return logs_dir


def _log_path() -> str:
    return os.path.join(_resolve_logs_dir(), _LOG_FILENAME)


def _append_log(header: str, body: str) -> str:
    path = _log_path()
    timestamp = _datetime.datetime.now().isoformat(timespec="seconds")
    try:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(f"\n===== {timestamp} {header} =====\n")
            handle.write(body)
            if not body.endswith("\n"):
                handle.write("\n")
    except OSError:
        pass
    return path


def log_warning(message: str) -> str:
    """Append a non-fatal warning to crash.log and return the file path."""
    return _append_log("WARNING", message)


def log_exception(exc_type, exc_value, tb) -> str:
    formatted = "".join(traceback.format_exception(exc_type, exc_value, tb))
    return _append_log("UNHANDLED EXCEPTION", formatted)


def _format_user_message(exc_type, exc_value, log_file: str) -> str:
    name = getattr(exc_type, "__name__", "Erro")
    detail = str(exc_value) or "(sem detalhes)"
    return (
        f"O ScreenChurch encontrou um erro inesperado e pode fechar.\n\n"
        f"Tipo: {name}\n"
        f"Detalhe: {detail}\n\n"
        f"O registro completo foi salvo em:\n{log_file}"
    )


def install_excepthook() -> None:
    """Install a sys.excepthook that logs and surfaces unhandled exceptions.

    Safe to call before QApplication exists: the message box is only shown
    when QApplication is already running. Otherwise only the log is written.
    """

    def hook(exc_type, exc_value, tb):
        # Always log first — even if showing the dialog fails later.
        log_file = log_exception(exc_type, exc_value, tb)

        try:
            from PyQt5.QtWidgets import QApplication, QMessageBox

            if QApplication.instance() is not None:
                QMessageBox.critical(
                    None,
                    "ScreenChurch — erro inesperado",
                    _format_user_message(exc_type, exc_value, log_file),
                )
        except Exception:
            # Never let the hook itself raise. The log is what matters.
            pass

        # Keep the original behavior for KeyboardInterrupt (Ctrl+C in dev).
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, tb)

    sys.excepthook = hook
