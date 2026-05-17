"""Background workers for ScreenChurch.

Large media imports (multi-gigabyte videos) cannot run on the Qt event loop:
they would freeze the UI and may be killed by Windows as "not responding".
This module copies files in chunks on a QThread, reports progress to a modal
QProgressDialog, and supports cancellation.
"""

from __future__ import annotations

import os
import re
import shutil

from PyQt5.QtCore import QObject, QThread, Qt, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QProgressDialog

from error_handler import log_warning


_CHUNK_BYTES = 4 * 1024 * 1024


class _CopyWorker(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, source: str, destination: str):
        super().__init__()
        self.source = source
        self.destination = destination
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            size = os.path.getsize(self.source) or 1
            copied = 0
            last_percent = -1
            with open(self.source, "rb") as src, open(self.destination, "wb") as dst:
                while True:
                    if self._cancelled:
                        break
                    chunk = src.read(_CHUNK_BYTES)
                    if not chunk:
                        break
                    dst.write(chunk)
                    copied += len(chunk)
                    percent = int(copied * 100 / size)
                    if percent != last_percent:
                        last_percent = percent
                        self.progress.emit(percent)
            if self._cancelled:
                try:
                    os.remove(self.destination)
                except OSError:
                    pass
                self.failed.emit("Cópia cancelada pelo operador.")
                return
            try:
                shutil.copystat(self.source, self.destination)
            except OSError:
                pass
            self.finished.emit(self.destination)
        except OSError as error:
            self.failed.emit(str(error))


def _unique_destination(folder: str, source: str) -> str:
    os.makedirs(folder, exist_ok=True)
    base = os.path.basename(source)
    name, ext = os.path.splitext(base)
    safe = re.sub(r"[^\w\-.]+", "_", name, flags=re.UNICODE).strip("_") or "arquivo"
    candidate = os.path.join(folder, safe + ext.lower())
    counter = 2
    while os.path.exists(candidate):
        candidate = os.path.join(folder, f"{safe}_{counter}{ext.lower()}")
        counter += 1
    return candidate


def copy_file_to_folder(parent, source: str, destination_folder: str, *,
                        title: str = "Copiando arquivo") -> str | None:
    """Copy `source` into `destination_folder` showing a modal progress dialog.

    Returns the destination path on success, or None on cancel/failure. The
    dialog keeps the Qt event loop responsive while a QThread performs the I/O.
    """
    if not source or not os.path.isfile(source):
        return None

    destination = _unique_destination(destination_folder, source)

    dialog = QProgressDialog(
        f"Copiando {os.path.basename(source)}…",
        "Cancelar",
        0,
        100,
        parent,
    )
    dialog.setWindowTitle(title)
    dialog.setWindowModality(Qt.WindowModal)
    dialog.setMinimumDuration(0)
    dialog.setAutoClose(True)
    dialog.setAutoReset(False)
    dialog.setValue(0)

    thread = QThread(parent)
    worker = _CopyWorker(source, destination)
    worker.moveToThread(thread)

    result = {"path": None, "error": None}

    def _on_finished(path: str) -> None:
        result["path"] = path
        thread.quit()

    def _on_failed(message: str) -> None:
        result["error"] = message
        thread.quit()

    thread.started.connect(worker.run)
    worker.progress.connect(dialog.setValue)
    worker.finished.connect(_on_finished)
    worker.failed.connect(_on_failed)
    dialog.canceled.connect(worker.cancel)
    thread.finished.connect(dialog.reset)
    thread.finished.connect(worker.deleteLater)

    thread.start()
    dialog.exec_()
    thread.wait(10_000)
    thread.deleteLater()

    if result["error"]:
        log_warning(f"Falha ao copiar {source} -> {destination}: {result['error']}")
        QMessageBox.warning(parent, "Erro ao copiar", result["error"])
        return None
    return result["path"]
