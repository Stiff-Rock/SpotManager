# TODO: MAKE A SINGLE SHARED STATIC DOWNLOADER THREAD
from PySide6 import QtCore
import requests


class DownloadCoverWorker(QtCore.QObject):
    finished = QtCore.Signal()
    on_cover_donwloaded = QtCore.Signal(bytes)

    def __init__(self):
        super().__init__()
        self.cover_url = ""

    @QtCore.Slot()
    def cancel(self):
        self._is_cancelled = True

    def run(self):
        cover_bytes = bytes()
        try:
            response = requests.get(self.cover_url)
            if response.status_code == 200:
                cover_bytes = response.content
                self.on_cover_donwloaded.emit(cover_bytes)
            else:
                print(f"Could not download cover with Url '{self.cover_url}'")
        except Exception as e:
            print(
                f"An error occurred while downloading the cover from '{self.cover_url}': {e}"
            )
        finally:
            self.finished.emit()

    def set_cover_url(self, cover_url: str):
        self.cover_url = cover_url


_COVER_DOWNLOAD_WORKER = DownloadCoverWorker()


def get_download_worker(cover_url: str):
    if not cover_url:
        raise Exception("Error: provide a cover url for the download worker")

    _COVER_DOWNLOAD_WORKER.set_cover_url(cover_url)
    return _COVER_DOWNLOAD_WORKER
