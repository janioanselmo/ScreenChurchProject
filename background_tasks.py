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
import urllib.request

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


class _ArchiveWorker(QObject):
    finished = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, base_name: str, root_dir: str):
        super().__init__()
        self.base_name = base_name
        self.root_dir = root_dir

    def run(self) -> None:
        try:
            path = shutil.make_archive(self.base_name, "zip", self.root_dir)
            self.finished.emit(path)
        except OSError as error:
            self.failed.emit(str(error))


def make_archive_in_background(parent, base_name: str, root_dir: str, *,
                               title: str = "Criando backup") -> str | None:
    """Run shutil.make_archive on a QThread with an indeterminate progress dialog.

    ZIP creation for a multi-GB ScreenChurchData folder takes long enough to
    freeze the UI synchronously; Windows can flag the app as "not responding".
    Returns the resulting archive path, or None on failure.
    """
    dialog = QProgressDialog(
        "Compactando dados em ZIP. Isto pode levar alguns minutos…",
        None,
        0,
        0,  # 0/0 = indeterminate (busy) bar
        parent,
    )
    dialog.setWindowTitle(title)
    dialog.setWindowModality(Qt.WindowModal)
    dialog.setMinimumDuration(0)
    dialog.setAutoClose(True)
    dialog.setAutoReset(False)
    dialog.setCancelButton(None)  # make_archive cannot be cancelled mid-flight

    thread = QThread(parent)
    worker = _ArchiveWorker(base_name, root_dir)
    worker.moveToThread(thread)

    result = {"path": None, "error": None}

    def _on_finished(path: str) -> None:
        result["path"] = path
        thread.quit()

    def _on_failed(message: str) -> None:
        result["error"] = message
        thread.quit()

    thread.started.connect(worker.run)
    worker.finished.connect(_on_finished)
    worker.failed.connect(_on_failed)
    thread.finished.connect(dialog.reset)
    thread.finished.connect(worker.deleteLater)

    thread.start()
    dialog.exec_()
    thread.wait(30_000)
    thread.deleteLater()

    if result["error"]:
        log_warning(f"Falha ao criar backup em {base_name}: {result['error']}")
        QMessageBox.warning(parent, "Backup", result["error"])
        return None
    return result["path"]


class _HttpFetchWorker(QObject):
    finished = pyqtSignal(bytes, str)
    failed = pyqtSignal(str)

    def __init__(self, url: str, headers: dict, timeout: int):
        super().__init__()
        self.url = url
        self.headers = headers or {}
        self.timeout = timeout

    def run(self) -> None:
        try:
            request = urllib.request.Request(self.url, headers=self.headers)
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                charset = response.headers.get_content_charset() or "utf-8"
            self.finished.emit(raw, charset)
        except Exception as error:
            self.failed.emit(str(error))


def fetch_url_in_background(parent, url: str, *, headers: dict = None,
                            timeout: int = 15,
                            title: str = "Buscando online"):
    """Run urllib.urlopen on a QThread with a modal progress dialog.

    Returns (raw_bytes, charset) on success, or (None, None) on failure/cancel.
    The dialog keeps the UI responsive while online song search / lyric fetch
    is in flight. Cancelling hides the dialog immediately but the worker can
    only stop on its own timeout — urlopen has no clean interrupt.
    """
    dialog = QProgressDialog("Buscando online…", "Cancelar", 0, 0, parent)
    dialog.setWindowTitle(title)
    dialog.setWindowModality(Qt.WindowModal)
    dialog.setMinimumDuration(200)  # avoid flashing for sub-200 ms responses
    dialog.setAutoClose(True)
    dialog.setAutoReset(False)

    thread = QThread(parent)
    worker = _HttpFetchWorker(url, headers or {}, timeout)
    worker.moveToThread(thread)

    result = {"raw": None, "charset": None, "error": None, "cancelled": False}

    def _on_finished(raw: bytes, charset: str) -> None:
        result["raw"] = raw
        result["charset"] = charset
        thread.quit()

    def _on_failed(message: str) -> None:
        result["error"] = message
        thread.quit()

    def _on_cancel() -> None:
        result["cancelled"] = True
        thread.quit()

    thread.started.connect(worker.run)
    worker.finished.connect(_on_finished)
    worker.failed.connect(_on_failed)
    dialog.canceled.connect(_on_cancel)
    thread.finished.connect(dialog.reset)
    thread.finished.connect(worker.deleteLater)

    thread.start()
    dialog.exec_()
    thread.wait(int((timeout + 2) * 1000))
    thread.deleteLater()

    if result["cancelled"] or result["error"]:
        if result["error"]:
            log_warning(f"Falha HTTP em {url}: {result['error']}")
        return None, None
    return result["raw"], result["charset"]
