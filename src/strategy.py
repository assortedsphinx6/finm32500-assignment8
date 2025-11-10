import os, socket, json, time, threading, collections
from src.shared_memory_utils import SharedPriceBook

HOST, NEWS_PORT, ORDER_PORT = "127.0.0.1", 5002, 5003
MESSAGE_DELIMITER = b"*"
SYMBOLS = ["AAPL", "MSFT", "GOOG", "AMZN"]
SHORT_WIN, LONG_WIN = 5, 15
BULLISH_THRESHOLD, BEARISH_THRESHOLD = 60, 40
PERF_LOG = "data/performance_log.txt"

def _recv_frames(conn):
    buf = b""
    while True:
        try:
            chunk = conn.recv(4096)
            if not chunk: break
            buf += chunk
            while MESSAGE_DELIMITER in buf:
                frame, buf = buf.split(MESSAGE_DELIMITER, 1)
                if frame: yield frame
        except Exception:
            break

def _ma(d, k):
    return sum(list(d)[-k:]) / k if len(d) >= k else None

def run_strategy():
    shm_name = os.environ.get("SHM_NAME")
    spb = SharedPriceBook(symbols=SYMBOLS, name=shm_name, create=False)
    os.makedirs("data", exist_ok=True)
    open("data/shm_name.txt", "w").write(spb.name)

    # Connect to news and order manager
    try:
        news_conn = socket.create_connection((HOST, NEWS_PORT))
    except Exception as e:
        with open(PERF_LOG, "a") as f:
            f.write(f"[Strategy] Failed to connect to NEWS: {e}\n")
        news_conn = None

    try:
        order_conn = socket.create_connection((HOST, ORDER_PORT))
    except Exception as e:
        with open(PERF_LOG, "a") as f:
            f.write(f"[Strategy] Failed to connect to ORDER manager: {e}\n")
        order_conn = None

    sentiment = 50
    missed_snapshots = 0
    latency_list = []
    order_count = 0
    news_connection_drops = 0
    order_connection_drops = 0

    # News listener thread
    def news_loop():
        nonlocal sentiment, news_connection_drops
        if not news_conn:
            return
        while True:
            try:
                for f in _recv_frames(news_conn):
                    try:
                        _, v = f.decode().split(",", 1)
                        sentiment = int(v)
                    except:
                        continue
            except Exception:
                news_connection_drops += 1
                time.sleep(0.5)

    threading.Thread(target=news_loop, daemon=True).start()

    hist = {s: collections.deque(maxlen=LONG_WIN) for s in SYMBOLS}
    pos = {s: None for s in SYMBOLS}

    try:
        while True:
            snap = spb.snapshot_consistent()
            if not snap:
                missed_snapshots += 1
                time.sleep(0.01)
                continue

            now = time.time()
            for s, px in snap.items():
                if px != px:  # skip NaN
                    continue
                px = float(px)
                hist[s].append(px)
                s_ma, l_ma = _ma(hist[s], SHORT_WIN), _ma(hist[s], LONG_WIN)
                if not s_ma or not l_ma:
                    continue

                price_sig = "BUY" if s_ma > l_ma else "SELL"
                news_sig = (
                    "BUY" if sentiment > BULLISH_THRESHOLD
                    else "SELL" if sentiment < BEARISH_THRESHOLD
                    else "HOLD"
                )

                if price_sig == news_sig == "BUY" and pos[s] != "long":
                    pos[s] = "long"
                    order = {"symbol": s, "side": "BUY", "qty": 10, "price": round(px, 4)}
                    if order_conn:
                        try:
                            order_conn.sendall(json.dumps(order).encode() + MESSAGE_DELIMITER)
                            latency_list.append(now - spb.read(s)[1])
                            order_count += 1
                        except Exception:
                            order_connection_drops += 1

                elif price_sig == news_sig == "SELL" and pos[s] != "short":
                    pos[s] = "short"
                    order = {"symbol": s, "side": "SELL", "qty": 10, "price": round(px, 4)}
                    if order_conn:
                        try:
                            order_conn.sendall(json.dumps(order).encode() + MESSAGE_DELIMITER)
                            latency_list.append(now - spb.read(s)[1])
                            order_count += 1
                        except Exception:
                            order_connection_drops += 1

            time.sleep(0.02)

    except KeyboardInterrupt:
        pass
    finally:
        with open(PERF_LOG, "a") as f:
            avg_latency = sum(latency_list)/len(latency_list) if latency_list else 0.0
            f.write(
                f"[Strategy] Processed {order_count} orders | Avg latency: {avg_latency:.4f}s | "
                f"Missed snapshots: {missed_snapshots} | "
                f"News drops: {news_connection_drops} | "
                f"Order drops: {order_connection_drops}\n"
            )
