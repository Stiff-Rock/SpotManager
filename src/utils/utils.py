from typing import Any

from PySide6 import QtCore


PLAYLISTS_JSON_PATH = "playlists.json"


def cleanup_thread(
    caller_instance: Any, worker_attr_name: str, thread_attr_name: str
) -> None:
    worker = getattr(caller_instance, worker_attr_name, None)
    logic_thread = getattr(caller_instance, thread_attr_name, None)

    if worker and isinstance(worker, QtCore.QObject):
        worker.deleteLater()

    if logic_thread and isinstance(logic_thread, QtCore.QThread):
        logic_thread.deleteLater()

    setattr(caller_instance, worker_attr_name, None)
    setattr(caller_instance, thread_attr_name, None)
