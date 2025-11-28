import os
import time
import shutil

class FileCache:
    def __init__(self, cache_dir='cache', ttl=86400):
        self.cache_dir = cache_dir
        self.ttl = ttl
        os.makedirs(self.cache_dir, exist_ok=True)

    def path(self, key: str):
        return os.path.join(self.cache_dir, key)

    def exists(self, key: str):
        path = self.path(key)
        if not os.path.exists(path):
            return False
        # TTL check
        if time.time() - os.path.getmtime(path) > self.ttl:
            try:
                os.remove(path)
            except Exception:
                pass
            return False
        return True

    def put(self, key: str, src_path: str):
        dst = self.path(key)
        shutil.copy2(src_path, dst)

    def cleanup(self):
        for fn in os.listdir(self.cache_dir):
            path = os.path.join(self.cache_dir, fn)
            try:
                if time.time() - os.path.getmtime(path) > self.ttl:
                    os.remove(path)
            except Exception:
                pass
