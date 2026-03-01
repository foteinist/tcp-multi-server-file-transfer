# TCP Multi-Server File Transfer System

A TCP-based multi-server file transfer system with performance evaluation under varying wireless network conditions.

This project implements a custom client–server architecture where a client retrieves files from two servers using a configurable request pattern. The system measures total transfer time, throughput, and analyzes performance under different wireless bottlenecks.

Developed as part of the course:
**Wireless Networks and Mobile Communications**  
Athens University of Economics and Business

---

## Overview

The system consists of:

- A multithreaded TCP server
- A TCP client with configurable request scheduling
- Custom application-layer protocol
- Automatic throughput calculation
- CSV logging of experiment runs
- Aggregated statistics & visualization
- Experimental evaluation report

The client requests 160 files (`sXXX.m4s`) from two servers using parameters:

- `n_A`: number of consecutive files requested from Server A
- `n_B`: number of consecutive files requested from Server B

This allows experimentation with different load distributions.

---

## Architecture

### Server

- TCP socket (IPv4)
- Multithreaded (one thread per connection)
- Custom protocol:
  - Client sends: `GET_FILE <filename>`
  - Server responds with:
    - 8-byte unsigned integer (file size, network byte order)
    - Raw file bytes

### Client

- Establishes a new TCP connection per file
- Requests files in configurable batches
- Measures:
  - Total transfer time
  - Total bytes transferred
  - Throughput (Mbps)
  - Success counts per server
- Logs results to `experiment_results.csv`
- Generates aggregated statistics and bar plots (if pandas/matplotlib installed)

---

## Project Structure

```
tcp-multi-server-file-transfer/
│
├── src/
│   ├── server.py
│   └── client.py
│
├── experiments/
│   └── report.pdf
│
├── README.md
├── RUNNING.md
├── requirements.txt
└── .gitignore
```

Generated files (not tracked by Git):

- `experiment_results.csv`
- `table_all.csv`
- `bar_all.png`
- `downloads/`

---

## Experimental Study

The accompanying report includes:

- Two experimental scenarios
- Different wireless configurations
- RSSI measurements
- TCP throughput measurements
- Bottleneck analysis
- Comparative evaluation

Key insight:
Performance is minimized when more files are requested from the higher-throughput server, demonstrating clear network bottleneck behavior.

---

## Key Concepts Demonstrated

- TCP socket programming
- Multithreading
- Custom application-layer protocol design
- Binary framing (8-byte size header)
- Throughput calculation
- Experimental performance evaluation
- Wireless bottleneck analysis
- Automated metrics logging

---

## Technologies Used

- Python 3
- TCP Sockets
- threading
- struct (binary protocol)
- pandas (optional)
- matplotlib (optional)

---

## Author

- Foteini Sotiropoulou  
