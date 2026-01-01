from spotdl import Optional
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.gui.widgets.playlist_card import SyncPlaylistsWorker


class CardSharedWorker:
    def __init__(self):
        self.shared_worker: Optional["SyncPlaylistsWorker"] = None


CARD_SHARED_WORKER = CardSharedWorker()
