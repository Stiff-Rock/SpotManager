from typing import Any
from PySide6 import QtCore

from src.utils.card_shared_worker import CARD_SHARED_WORKER


@QtCore.Slot()
def cleanup_thread(
    caller_instance: Any, worker_attr_name: str, thread_attr_name: str
) -> None:
    # Cleanup the worker
    if worker_attr_name != "shared_worker":
        worker = getattr(caller_instance, worker_attr_name, None)
        if worker and isinstance(worker, QtCore.QObject):
            worker.deleteLater()
        setattr(caller_instance, worker_attr_name, None)
    else:
        if CARD_SHARED_WORKER.shared_worker and isinstance(
            CARD_SHARED_WORKER.shared_worker, QtCore.QObject
        ):
            CARD_SHARED_WORKER.shared_worker.deleteLater()
        CARD_SHARED_WORKER.shared_worker = None

    # Cleanup the logic thread
    logic_thread = getattr(caller_instance, thread_attr_name, None)
    if logic_thread and isinstance(logic_thread, QtCore.QThread):
        logic_thread.deleteLater()
    setattr(caller_instance, thread_attr_name, None)
