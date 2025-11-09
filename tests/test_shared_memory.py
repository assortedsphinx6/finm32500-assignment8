# tests/test_shared_memory.py
from src.shared_memory_utils import SharedPriceBook, SYMBOLS
import time

def test_shared_pricebook_update_and_read():
    spb = SharedPriceBook(SYMBOLS, name=None, create=True)
    try:
        spb.update("AAPL", 123.45)
        # small wait for memory to be written
        time.sleep(0.01)
        snap = spb.snapshot_consistent()
        assert snap is not None
        assert abs(float(snap["AAPL"]) - 123.45) < 1e-6
    finally:
        try:
            spb.close()
            spb.unlink()
        except Exception:
            pass
