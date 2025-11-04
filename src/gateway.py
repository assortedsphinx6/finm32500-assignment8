import socket
import threading
import time
import random

HOST = "127.0.0.1"
PRICE_PORT = 5001
NEWS_PORT  = 5002
MESSAGE_DELIMITER = b"*"

SYMBOLS = ["AAPL", "MSFT", "GOOG", "AMZN"]
TICK_INTERVAL_SEC = 0.2  

def _serve(port, frames_fn, name):
    """Minimal TCP broadcast server: accepts clients and sends each frame + delimiter."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, port))
    srv.listen()
    print(f"[Gateway:{name}] listening on {HOST}:{port}")

    clients = []
    lock = threading.Lock()

    def accept_loop():
        while True:
            conn, addr = srv.accept()
            print(f"[Gateway:{name}] client {addr} connected")
            with lock:
                clients.append(conn)

    threading.Thread(target=accept_loop, daemon=True).start()

    for frame in frames_fn():
        data = frame + MESSAGE_DELIMITER
        dead = []
        with lock:
            for c in clients:
                try:
                    c.sendall(data)
                except Exception:
                    dead.append(c)
            for c in dead:
                try:
                    c.close()
                except Exception:
                    pass
                clients.remove(c)

def price_frames():
    levels = {s: 100.0 + random.random() * 10 for s in SYMBOLS}
    while True:
        for s in SYMBOLS:
            levels[s] = max(0.01, levels[s] + random.gauss(0.0, 0.15))
        msg = "*".join(f"{s},{levels[s]:.4f}" for s in SYMBOLS).encode("utf-8")
        yield msg
        time.sleep(TICK_INTERVAL_SEC)

def news_frames():
    while True:
        yield f"NEWS,{random.randint(0,100)}".encode("utf-8")
        time.sleep(TICK_INTERVAL_SEC)

def run_gateway():
    t1 = threading.Thread(target=_serve, args=(PRICE_PORT, price_frames, "prices"), daemon=True)
    t2 = threading.Thread(target=_serve, args=(NEWS_PORT,  news_frames,  "news"),   daemon=True)
    t1.start(); t2.start()
    print("[Gateway] running (prices:5001, news:5002). Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Gateway] stopping.")

if __name__ == "__main__":
    run_gateway()