# tests/test_connections.py
import threading, time, socket, importlib
from tests.test_utils import find_free_port, wait_for_port

def test_gateway_and_ordermanager_accept_connections():
    # pick ephemeral ports
    price_port = find_free_port()
    news_port = find_free_port()
    order_port = find_free_port()

    # import modules and set ports BEFORE starting
    import src.gateway as gateway
    import src.order_manager as om

    importlib.reload(gateway)
    importlib.reload(om)

    gateway.PRICE_PORT = price_port
    gateway.NEWS_PORT = news_port
    om.ORDER_PORT = order_port

    # start servers in background threads
    t_gw = threading.Thread(target=gateway.run_gateway, daemon=True)
    t_om = threading.Thread(target=om.run_ordermanager, daemon=True)
    t_gw.start()
    t_om.start()

    assert wait_for_port(gateway.HOST, price_port, timeout=3.0), "Gateway price port not listening"
    assert wait_for_port(gateway.HOST, news_port, timeout=3.0), "Gateway news port not listening"
    assert wait_for_port("127.0.0.1", order_port, timeout=3.0), "OrderManager port not listening"

    # quick connect test
    s1 = socket.create_connection((gateway.HOST, price_port), timeout=2.0)
    s1.close()
    s2 = socket.create_connection((gateway.HOST, news_port), timeout=2.0)
    s2.close()
    s3 = socket.create_connection(("127.0.0.1", order_port), timeout=2.0)
    s3.close()
