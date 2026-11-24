"""Minimal seekable read-only file over HTTP Range requests (lets pyarrow read only needed parquet columns)."""
import io
import time

import requests


class HTTPRangeFile(io.RawIOBase):
    def __init__(self, url, session=None, block=8 * 1024 * 1024):
        self.url = url
        self.s = session or requests.Session()
        self.s.headers.setdefault("User-Agent", "accelerator-research")
        r = self.s.head(url, allow_redirects=True, timeout=60)
        r.raise_for_status()
        self.url = r.url
        self.size = int(r.headers["Content-Length"])
        self.pos = 0
        self.block = block
        self.cache = {}
        self.nreq = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else (self.pos + off if whence == 1 else self.size + off)
        return self.pos

    def _get_block(self, i):
        if i not in self.cache:
            start = i * self.block
            end = min(self.size, start + self.block) - 1
            for attempt in range(5):
                try:
                    r = self.s.get(self.url, headers={"Range": f"bytes={start}-{end}"}, timeout=120)
                    if r.status_code in (200, 206):
                        break
                except requests.RequestException:
                    pass
                time.sleep(3 * (attempt + 1))
            r.raise_for_status()
            self.nreq += 1
            time.sleep(0.2)
            if len(self.cache) > 64:
                self.cache.clear()
            self.cache[i] = r.content
        return self.cache[i]

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        n = max(0, min(n, self.size - self.pos))
        out = bytearray()
        while n > 0:
            i, o = divmod(self.pos, self.block)
            b = self._get_block(i)[o:o + n]
            out += b
            self.pos += len(b)
            n -= len(b)
        return bytes(out)

    def readinto(self, buf):
        d = self.read(len(buf))
        buf[: len(d)] = d
        return len(d)
