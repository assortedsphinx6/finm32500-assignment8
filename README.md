# finm32500-assignment8
Interprocess Communication for Trading Systems
This project implements a simple multi-process trading simulation using shared memory and TCP sockets. Independent components exchange market data, sentiment, and orders in real time, while tracking latency, throughput, and reliability.

Flowchart/Diagram:

Gateway (Prices & News)
        |
        v
OrderBook (Shared Memory)
        |
        v
Strategy (Decision Logic)
        |
        v
OrderManager (Orders)

Components
Price Server: streams synthetic price ticks
OrderBook: writes prices to shared memory and logs throughput
NewsFeed: broadcasts sentiment updates
Strategy: consumes prices and sentiment to place trades
Analyzer: summarizes performance metrics

Run Instructions
Install dependencies:
pip install -r requirements.txt
Start the components in separate terminals:
python src/priceserver.py
python src/orderbook.py
python src/newsfeed.py
python src/strategy.py
Let the system run for ~30 seconds, then analyze:
python analyze_performance.py

Outputs
data/performance_log.txt — live logs of throughput, latency, and errors
performance_report.md — summary of benchmarks
video.mp4 — demonstration of the full system running

Example Log
[OrderBook] Throughput: 19.6 ticks/sec | SHM size: 16.00 KB
[Strategy] Processed 164 orders | Avg latency: 0.0567s | Missed snapshots: 0 | News drops: 0 | Order drops: 0

Reliability
Automatically reconnects on dropped sockets
Handles missing or stale data gracefully
Logs all recovery events for performance analysis

