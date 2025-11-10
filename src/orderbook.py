import socket, time, os
from src.shared_memory_utils import SharedPriceBook, SYMBOLS

MESSAGE_DELIMITER = b"*"
HOST = "127.0.0.1"
PRICE_PORT = 5001
PERF_LOG = "data/performance_log.txt"

def _recv_frames(conn):
    buf = b""
    while True:
        chunk = conn.recv(4096)
        if not chunk: break
        buf += chunk
        while MESSAGE_DELIMITER in buf:
            frame, buf = buf.split(MESSAGE_DELIMITER, 1)
            if frame: yield frame

def run_orderbook():
    spb = SharedPriceBook(symbols=SYMBOLS, create=True)

    os.makedirs("data", exist_ok=True)
    with open("data/shm_name.txt", "w") as f:
        f.write(spb.name)
        f.flush()
        os.fsync(f.fileno())

    print(f"[OrderBook] SharedMemory name: {spb.name}")
    print(f"[OrderBook] Symbols: {', '.join(spb.symbols)}")

    tick_count = 0
    start_time = time.time()
    dropped_connections = 0
    downtime_duration = 0.0
    missed_ticks = 0

    while True:
        try:
            with socket.create_connection((HOST, PRICE_PORT), timeout=3) as conn:
                conn_start = time.time()
                for frame in _recv_frames(conn):
                    parts = frame.decode("utf-8").split("*")
                    if not parts:
                        missed_ticks += 1
                    for p in parts:
                        if not p: continue
                        try:
                            sym, px = p.split(",", 1)
                            if sym in spb.idx:
                                ts = time.time()
                                spb.update(sym, float(px), timestamp=ts)
                                tick_count += 1
                        except ValueError:
                            missed_ticks += 1

                    # log every 5s to file
                    elapsed = time.time() - start_time
                    if elapsed >= 5.0:
                        throughput = tick_count / elapsed
                        with open(PERF_LOG, "a") as f:
                            f.write(
                                f"[OrderBook] Throughput: {throughput:.2f} ticks/sec | "
                                f"SHM size: {spb.shm.size/1024:.2f} KB | "
                                f"Dropped connections: {dropped_connections} | "
                                f"Missed ticks: {missed_ticks} | "
                                f"Downtime: {downtime_duration:.2f}s\n"
                            )
                        tick_count = 0
                        missed_ticks = 0
                        start_time = time.time()
        except Exception as e:
            dropped_connections += 1
            dt_start = time.time()
            with open(PERF_LOG, "a") as f:
                f.write(f"[OrderBook] Connection lost: {e}. Retrying …\n")
            time.sleep(0.5)
            downtime_duration += time.time() - dt_start

if __name__ == "__main__":
    run_orderbook()
