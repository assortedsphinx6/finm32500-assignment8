import socket
import threading
import json

HOST = "127.0.0.1"
ORDER_PORT = 5003
MESSAGE_DELIMITER = b"*"

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

def _handle(conn, addr):
    print(f"[OrderManager] client {addr} connected")
    for frame in _recv_frames(conn):
        try:
            order = json.loads(frame.decode("utf-8"))
            print(f"Received Order: {order.get('side')} {order.get('qty')} {order.get('symbol')} @ {order.get('price')}")
        except Exception as e:
            print(f"[OrderManager] bad payload: {e}")
    try:
        conn.close()
    except Exception:
        pass

def run_ordermanager():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, ORDER_PORT))
    srv.listen()
    print(f"[OrderManager] listening on {HOST}:{ORDER_PORT}")
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=_handle, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    run_ordermanager()