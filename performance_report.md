# Performance Report
Generated on: **2025-11-09 21:37:33**

## 1. Overview
| Metric | Value |
|--------|-------|
| Total Strategy Orders | 838 |
| Log Entries | 32 |
| Symbols | AAPL, MSFT, GOOG, AMZN |

---

## 2. Latency Benchmark
| Statistic | Latency (s) |
|------------|-------------|
| Average | 0.0691 |
| Min | 0.0691 |
| Max | 0.0691 |

---

## 3. Throughput
| Statistic | Ticks / sec |
|------------|-------------|
| Average | 19.6294 |
| Min | 19.51 |
| Max | 19.71 |

---

## 4. Memory Usage
| Metric | Value (KB) |
|---------|------------|
| Average SHM Size | 16.0 |
| Max SHM Size | 16.0 |

---

## 5. Reliability
| Event | Count |
|--------|-------|
| Missed Snapshots | 4 |
| News Drops | 0 |
| Order Drops | 0 |

System maintained stable throughput and latency even under reconnections.

---

## 6. Notes
- Logs were collected automatically during live trading simulation.
- Throughput is computed over 5-second intervals.
- Latency measured between tick timestamp and trade decision time.
