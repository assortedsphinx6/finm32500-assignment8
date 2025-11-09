import os, time
from multiprocessing import Process
from src.gateway import run_gateway
from src.order_manager import run_ordermanager
from src.orderbook import run_orderbook
from src.strategy import run_strategy

def _wait_for_shm_name(path="data/shm_name.txt", timeout=10.0):
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
    procs = []

    p_gw = Process(target=run_gateway, daemon=True)
    p_gw.start(); procs.append(p_gw)

    p_om = Process(target=run_ordermanager, daemon=True)
    p_om.start(); procs.append(p_om)

    p_ob = Process(target=run_orderbook, daemon=True)
    p_ob.start(); procs.append(p_ob)

    shm_name = _wait_for_shm_name(timeout=30.0)
    os.environ["SHM_NAME"] = shm_name
    p_strat = Process(target=run_strategy, daemon=True)
    p_strat.start(); procs.append(p_strat)

    try:
        for p in procs:
            p.join()
    except KeyboardInterrupt:
        pass