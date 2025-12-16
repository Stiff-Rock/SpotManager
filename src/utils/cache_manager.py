import os


class CacheManager:
    CACHE_DIR = "cache/covers"

    def __init__(self):
        if not os.path.exists(self.CACHE_DIR):
            os.makedirs(self.CACHE_DIR, exist_ok=True)

    def get_cover(self, file_name: str):
        cache_path = os.path.join(self.CACHE_DIR, f"{file_name}.jpg")
        if os.path.exists(cache_path):
            with open(cache_path, "rb") as f:
                return f.read()
        return None

    def save_cover(self, cover_bytes: bytes, file_name: str):
        if not cover_bytes:
            return
        cache_path = os.path.join(self.CACHE_DIR, f"{file_name}.jpg")
        with open(cache_path, "wb") as f:
            f.write(cover_bytes)

    def delete_cache_of_playlist(self, file_name: str):
        cache_path = os.path.join(self.CACHE_DIR, f"{file_name}.jpg")
        try:
            if os.path.exists(cache_path):
                os.remove(cache_path)
        except OSError as e:
            print(f"Error deleting cache file {cache_path}: {e}")


CACHE = CacheManager()
