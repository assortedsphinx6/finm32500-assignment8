import os, time
from multiprocessing import Process, Queue
from src.gateway import run_gateway
from src.orderbook import run_orderbook
from src.strategy import run_strategy
from src.order_manager import run_ordermanager

def _wait_for_shm_name(path="data/shm_name.txt", timeout=10.0):
    """Wait for the OrderBook to write the shared memory name."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with open(path, "r") as f:
                name = f.read().strip()
                if name:
                    return name
        except FileNotFoundError:
            pass
        time.sleep(0.1)
    raise RuntimeError("Timed out waiting for shared memory name file at data/shm_name.txt")

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    try:
        os.remove("data/shm_name.txt")
    except FileNotFoundError:
        pass

    processes = []

    # 1️⃣ Start Gateway
    print("Starting Gateway...")
    p_gw = Process(target=run_gateway, daemon=True)
    p_gw.start(); processes.append(p_gw)
    time.sleep(1)

    # 2️⃣ Start OrderManager
    print("Starting OrderManager...")
    p_om = Process(target=run_ordermanager, daemon=True)
    p_om.start(); processes.append(p_om)
    time.sleep(0.5)

    # 3️⃣ Start OrderBook
    print("Starting OrderBook...")
    p_ob = Process(target=run_orderbook, daemon=True)
    p_ob.start(); processes.append(p_ob)

    # 4️⃣ Wait for SHM_NAME
    shm_name = _wait_for_shm_name(timeout=30.0)
    os.environ["SHM_NAME"] = shm_name
    print(f"[Main] Received SHM_NAME={shm_name}")
    time.sleep(1)

    # 5️⃣ Start Strategy
    print("Starting Strategy...")
    p_strat = Process(target=run_strategy, daemon=True)
    p_strat.start(); processes.append(p_strat)
    time.sleep(0.5)

    print("\n✅ All processes started. System running...\n")

    # 6️⃣ Monitor performance periodically
    try:
        while True:
            time.sleep(5)
            # Optional: you could also implement a file or queue-based collection of
            # strategy latency and order throughput if you want to aggregate here.
            # For now, OrderBook and Strategy already print metrics every second.
    except KeyboardInterrupt:
        print("\n🔻 Stopping all processes...")

    finally:
        for p in processes:
            if p.is_alive():
                p.terminate()
        print("✅ All processes terminated cleanly.")
