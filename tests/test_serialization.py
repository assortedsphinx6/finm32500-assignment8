# tests/test_serialization.py
import socket, threading, json, time
from tests.test_utils import find_free_port

DELIM = b"*"

def run_receiver(port, received):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(1)
    conn, _ = srv.accept()
    buf = b""
    while True:
        data = conn.recv(4096)
        if not data:
            break
        buf += data
        while DELIM in buf:
            part, buf = buf.split(DELIM, 1)
            try:
                received.append(json.loads(part.decode()))
            except Exception:
                pass
    conn.close()
    srv.close()

def test_framed_json_roundtrip():
    port = find_free_port()
    received = []
    t = threading.Thread(target=run_receiver, args=(port, received), daemon=True)
    t.start()
    time.sleep(0.05)
    client = socket.create_connection(("127.0.0.1", port), timeout=2.0)
    o1 = {"id": 1, "symbol": "AAPL", "side": "BUY"}
    o2 = {"id": 2, "symbol": "MSFT", "side": "SELL"}
    client.sendall(json.dumps(o1).encode() + DELIM + json.dumps(o2).encode() + DELIM)
    client.shutdown(socket.SHUT_WR)
    client.close()
    time.sleep(0.1)
    assert any(o.get("id") == 1 for o in received)
    assert any(o.get("id") == 2 for o in received)
