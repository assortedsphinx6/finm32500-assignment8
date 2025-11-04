import socket
import time

MESSAGE_DELIMITER = b"*"
HOST = "127.0.0.1"
PRICE_PORT = 5001

from src.shared_memory_utils import SharedPriceBook, SYMBOLS

def _recv_frames(conn):
    buf = b""
    while True:
        chunk = conn.recv(4096)
        if not chunk:
            break
        buf += chunk
        while True:
            if MESSAGE_DELIMITER in buf:
                frame, buf = buf.split(MESSAGE_DELIMITER, 1)
                if frame:
                    yield frame
            else:
                break

def run_orderbook():
    spb = SharedPriceBook(symbols=SYMBOLS, create=True)
    print(f"[OrderBook] SharedMemory name: {spb.name}")
    print(f"[OrderBook] Symbols: {', '.join(spb.symbols)}")

    while True:
        try:
            print(f"[OrderBook] Connecting to Gateway at {HOST}:{PRICE_PORT} …")
            with socket.create_connection((HOST, PRICE_PORT), timeout=3) as conn:
                print("[OrderBook] Connected to price stream.")
                for frame in _recv_frames(conn):
                    parts = frame.decode("utf-8").split("*")
                    for p in parts:
                        if not p:
                            continue
                        try:
                            sym, px = p.split(",", 1)
                            if sym in spb.idx:
                                spb.update(sym, float(px))
                        except ValueError:
                            continue
        except Exception as e:
            print(f"[OrderBook] Connection issue: {e}. Retrying in 0.5s …")
            time.sleep(0.5)

if __name__ == "__main__":
    run_orderbook()