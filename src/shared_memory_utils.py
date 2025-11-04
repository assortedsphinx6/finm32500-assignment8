from multiprocessing import shared_memory, Lock
import numpy as np


SYMBOLS = ["AAPL", "MSFT", "GOOG", "AMZN"]
SYMBOL_BYTES = 8  

class SharedPriceBook:
    def __init__(self, symbols=SYMBOLS, name=None, create=True):
        self.symbols = list(symbols)
        self.n = len(self.symbols)
        self._writer_lock = Lock() 

        header = 16
        symtab = SYMBOL_BYTES * self.n
        prices = 8 * self.n  
        total = header + symtab + prices

        if create and name is None:
            self.shm = shared_memory.SharedMemory(create=True, size=total)
            self.name = self.shm.name
            self._buf = self.shm.buf
            np.ndarray((1,), dtype=np.int64, buffer=self._buf, offset=0)[0] = 0  
            np.ndarray((1,), dtype=np.int32, buffer=self._buf, offset=8)[0] = self.n
            base = 16
            for i, s in enumerate(self.symbols):
                raw = s.encode("utf-8")[:SYMBOL_BYTES]
                raw += b"\x00" * (SYMBOL_BYTES - len(raw))
                self._buf[base + i*SYMBOL_BYTES : base + (i+1)*SYMBOL_BYTES] = raw
            self.prices_view()[:] = np.nan
        else:
            self.shm = shared_memory.SharedMemory(name=name)
            self.name = name
            self._buf = self.shm.buf
            n = int(np.ndarray((1,), dtype=np.int32, buffer=self._buf, offset=8)[0])
            base = 16
            syms = []
            for i in range(n):
                raw = bytes(self._buf[base + i*SYMBOL_BYTES : base + (i+1)*SYMBOL_BYTES])
                syms.append(raw.split(b"\x00", 1)[0].decode("utf-8"))
            self.symbols = syms
            self.n = n

        self.idx = {s: i for i, s in enumerate(self.symbols)}

    def _seq_view(self):
        return np.ndarray((1,), dtype=np.int64, buffer=self._buf, offset=0)

    def prices_view(self):
        offset = 16 + SYMBOL_BYTES * self.n
        return np.ndarray((self.n,), dtype=np.float64, buffer=self._buf, offset=offset)


    def update(self, symbol: str, price: float):
        i = self.idx[symbol]
        with self._writer_lock:
            seq = self._seq_view()
            seq[0] += 1              
            self.prices_view()[i] = float(price)
            seq[0] += 1               

    def snapshot_consistent(self):
        seq0 = int(self._seq_view()[0])
        if seq0 % 2 == 1:
            return None
        snap = self.prices_view().copy()
        seq1 = int(self._seq_view()[0])
        if seq0 == seq1 and seq1 % 2 == 0:
            return dict(zip(self.symbols, snap))
        return None

    def close(self):
        self.shm.close()

    def unlink(self):
        self.shm.unlink()