import os, socket, json, time, threading, collections
from src.shared_memory_utils import SharedPriceBook

HOST, NEWS_PORT, ORDER_PORT = "127.0.0.1", 5002, 5003
MESSAGE_DELIMITER = b"*"
SYMBOLS = ["AAPL", "MSFT", "GOOG", "AMZN"]
SHORT_WIN, LONG_WIN = 5, 15
BULLISH_THRESHOLD, BEARISH_THRESHOLD = 60, 40

def _recv_frames(conn):
    buf = b""
    while True:
        chunk = conn.recv(4096)
        if not chunk: break
        buf += chunk
        while MESSAGE_DELIMITER in buf:
            frame, buf = buf.split(MESSAGE_DELIMITER, 1)
            if frame: yield frame

def _ma(d, k):
    return sum(list(d)[-k:]) / k if len(d) >= k else None

def run_strategy():
    shm_name = os.environ.get("SHM_NAME")
    spb = SharedPriceBook(symbols=SYMBOLS, name=shm_name, create=False)
    print(f"[Strategy] SHM={shm_name}")
    open("data/shm_name.txt", "w").write(spb.name)

    news_conn = socket.create_connection((HOST, NEWS_PORT))
    order_conn = socket.create_connection((HOST, ORDER_PORT))
    print("[Strategy] connected")

    sentiment = 50
    def news_loop():
        nonlocal sentiment
        for f in _recv_frames(news_conn):
            try: _, v = f.decode().split(",", 1); sentiment = int(v)
            except: pass
    threading.Thread(target=news_loop, daemon=True).start()

    hist = {s: collections.deque(maxlen=LONG_WIN) for s in SYMBOLS}
    pos = {s: None for s in SYMBOLS}
    while True:
        snap = spb.snapshot_consistent()
        if not snap: continue
        for s, px in snap.items():
            if px != px: continue
            px = float(px); hist[s].append(px)
            s_ma, l_ma = _ma(hist[s], SHORT_WIN), _ma(hist[s], LONG_WIN)
            if not s_ma or not l_ma: continue
            price_sig = "BUY" if s_ma > l_ma else "SELL"
            news_sig = "BUY" if sentiment > BULLISH_THRESHOLD else "SELL" if sentiment < BEARISH_THRESHOLD else "HOLD"
            if price_sig == news_sig == "BUY" and pos[s] != "long":
                pos[s] = "long"
                print(f"[Strategy] BUY {s} @ {round(px,4)}")
                order_conn.sendall(json.dumps({"symbol": s, "side": "BUY", "qty": 10, "price": round(px,4)}).encode()+MESSAGE_DELIMITER)
            elif price_sig == news_sig == "SELL" and pos[s] != "short":
                pos[s] = "short"
                print(f"[Strategy] SELL {s} @ {round(px,4)}")
                order_conn.sendall(json.dumps({"symbol": s, "side": "SELL", "qty": 10, "price": round(px,4)}).encode()+MESSAGE_DELIMITER)
                
        time.sleep(0.02)

if __name__ == "__main__":
    run_strategy()