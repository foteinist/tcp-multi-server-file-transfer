# Running Guide – TCP Multi-Server File Transfer

This document explains how to run the server, client, and experiments.

---

## Prerequisites

- Python 3.8+
- (Optional) pandas
- (Optional) matplotlib

Install optional dependencies:

```bash
pip install -r requirements.txt
```

---

## 1. Start the Servers

You must start one server per machine (or port).

From the `src/` directory:

```bash
python server.py <port>
```

Example:

```bash
python server.py 9000
```

The server listens on all interfaces (`0.0.0.0`).

Make sure the files (`sXXX.m4s`) exist in the same directory where the server runs.

---

## 2. Run the Client

From the `src/` directory:

```bash
python client.py n_A n_B IP_A IP_B [port_A] [port_B]
```

Example:

```bash
python client.py 3 1 192.168.1.10 192.168.1.13 9000 9000
```

Parameters:

- `n_A` → number of files requested consecutively from Server A
- `n_B` → number of files requested consecutively from Server B
- `IP_A` → IP address of Server A
- `IP_B` → IP address of Server B
- `port_A` (optional, default 9000)
- `port_B` (optional, default 9000)

The client will:

- Download 160 files
- Measure total time
- Compute throughput (Mbps)
- Save results to `experiment_results.csv`
- Generate aggregated statistics and bar plot (if pandas installed)

---

## Output Files (Generated Automatically)

After execution, the following files are created in the project root:

- `experiment_results.csv`
- `table_all.csv`
- `bar_all.png`
- `downloads/` (downloaded files)

These files are ignored by Git.

---

## Custom Protocol Summary

Client request:
```
GET_FILE filename
```

Server response:
- 8-byte unsigned integer (file size)
- Raw file bytes

If file not found:
- Server sends size = 0

---

## Notes

- A new TCP connection is created per file.
- Server is multithreaded.
- Throughput is computed as:

```
(total_bytes * 8) / (total_time * 1_000_000)
```

---

## Troubleshooting

- Ensure ports are open
- Ensure files exist on server side
- Ensure IP addresses are correct
- Check firewall settings