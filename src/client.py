# Usage: python client.py n_A n_B IP_A IP_B [port_A] [port_B]

import socket
import struct
import sys
import time
import os

#Διασφαλίζει ότι διαβάζεις ακριβώς n bytes από το socket. Το recv() δεν εγγυάται ότι θα επιστρέψει όλα τα bytes σε μία κλήση, οπότε αυτή η συνάρτηση επαναλαμβάνει μέχρι να συγκεντρωθούν n bytes ή να τερματιστεί η σύνδεση
#Το πρωτόκολλό μας στέλνει πρώτα 8 bytes (μέγεθος). Χρειάζεται να διαβάσουμε και τα 8, όχι λιγότερα
#Αν recv() επιστρέψει b'' σημαίνει ότι το socket έκλεισε, επιστρέφουμε None για να υποδείξουμε σφάλμα
def recv_all(sock, n):
    """Receive exactly n bytes.""" 
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data

#Νέα σύνδεση για κάθε αρχείο
def request_file(ip, port, filename, out_dir):
    """Request a single file from server ip:port."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Δημιουργούμε νέο TCP socket
    sock.settimeout(60) #Θέτουμε timeout 60s για να μην μπλοκάρει για πάντα
    sock.connect((ip, port)) #Σύνδεση στον server ip:port

    #Send request
    request = f"GET_FILE {filename}\n"
    sock.sendall(request.encode())

    #Receive size (8 bytes)
    size_data = recv_all(sock, 8) #Χρησιμοποιούμε recv_all για να πάρουμε ακριβώς 8 bytes
    if size_data is None:
        sock.close()
        raise RuntimeError("Did not receive file size!")

    size = struct.unpack("!Q", size_data)[0] #Μετατρέπει τα 8 bytes σε unsigned 64-bit integer (network byte order)

    if size == 0:
        sock.close()
        raise FileNotFoundError(f"File not found: {filename}")

    #Prepare output path
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)

    #Receive file data
    remaining = size
    start = time.time()
    with open(out_path, "wb") as f: #Άνοιγμα αρχείου σε binary write
        while remaining > 0: #Διάβασμα δεδομένων σε μπλοκ μέχρι να γράψεις size bytes
            chunk = sock.recv(min(65536, remaining))
            if not chunk: #Αν recv() επιστρέψει κενά (πρόωρο κλείσιμο), error
                sock.close()
                raise RuntimeError("Connection closed before file finished!")
            f.write(chunk)
            remaining -= len(chunk)
    duration = time.time() - start

    sock.close()
    return size, duration


import csv
RESULTS_CSV = "experiment_results.csv"

# optional plotting libs
try:
    import pandas as pd
    import matplotlib.pyplot as plt
except Exception:
    pd = None
    plt = None

def ensure_results_csv():
    header = ["timestamp","n_A","n_B","IP_A","IP_B","port_A","port_B",
              "total_time_s","total_bytes","throughput_Mbps","success_A","success_B","bytes_A","bytes_B"]
    if not os.path.exists(RESULTS_CSV):
        with open(RESULTS_CSV, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)

def append_result_row(rowdict):
    ensure_results_csv()
    with open(RESULTS_CSV, "a", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            rowdict.get("timestamp",""),
            rowdict.get("n_A",""),
            rowdict.get("n_B",""),
            rowdict.get("IP_A",""),
            rowdict.get("IP_B",""),
            rowdict.get("port_A",""),
            rowdict.get("port_B",""),
            f"{rowdict.get('total_time',0):.4f}",
            int(rowdict.get("total_bytes",0)),
            f"{rowdict.get('throughput_mbps',0):.4f}",
            rowdict.get("success_A",0),
            rowdict.get("success_B",0),
            int(rowdict.get("bytes_A",0)),
            int(rowdict.get("bytes_B",0))
        ])

def plot_aggregate():
    if pd is None or plt is None:
        print("[WARN] pandas or matplotlib not installed — skipping plotting.")
        return
    df = pd.read_csv(RESULTS_CSV)
    if df.empty:
        print("[WARN] No results to plot.")
        return
    # make label column nA-nB
    df["label"] = df["n_A"].astype(str) + "-" + df["n_B"].astype(str)
    agg = df.groupby("label").agg({"total_time_s":"mean","total_bytes":"mean","throughput_Mbps":"mean"}).reset_index()
    # save table
    agg.to_csv("table_all.csv", index=False)
    print("[INFO] Saved aggregated table -> table_all.csv")
    # bar plot mean total_time per label
    plt.figure(figsize=(10,5))
    plt.bar(agg["label"], agg["total_time_s"])
    plt.xlabel("n_A - n_B")
    plt.ylabel("Mean total time (s)")
    plt.title("Mean total time per n_A:n_B (aggregated runs)")
    plt.tight_layout()
    plt.savefig("bar_all.png")
    plt.close()
    print("[INFO] Saved bar chart -> bar_all.png")

# ---- τέλος προσθηκών ----


def main():
    if len(sys.argv) < 5:
        print("Usage: python client.py n_A n_B IP_A IP_B [port_A] [port_B]")
        return

    n_A = int(sys.argv[1])
    n_B = int(sys.argv[2])
    IP_A = sys.argv[3]
    IP_B = sys.argv[4]
    port_A = int(sys.argv[5]) if len(sys.argv) > 5 else 9000
    port_B = int(sys.argv[6]) if len(sys.argv) > 6 else 9000

    total_files = 160
    current = 1

    out_dir = "downloads"
    os.makedirs(out_dir, exist_ok=True)

    print(f"Starting download of {total_files} files...")
    print(f"Pattern: {n_A} from A ({IP_A}) then {n_B} from B ({IP_B})")

    start = time.time()

    # new stats
    bytes_A = 0
    bytes_B = 0
    success_A = 0
    success_B = 0

    while current <= total_files: #Επαναλαμβάνoyme μέχρι current > 160
    #Για κάθε αίτημα εκτυπώνουμε ποιο αρχείο ζητήθηκε
        #Batch from A
        for _ in range(n_A):
            if current > total_files:
                break
            filename = f"s{current:03d}.m4s"
            print(f"[A] Requesting {filename}")
            try:
                size, dur = request_file(IP_A, port_A, filename, out_dir)
                bytes_A += size
                success_A += 1
            except Exception as e:
                print(f"[ERROR] A {filename}: {e}")
            current += 1

        #Batch from B
        for _ in range(n_B):
            if current > total_files:
                break
            filename = f"s{current:03d}.m4s"
            print(f"[B] Requesting {filename}")
            try:
                size, dur = request_file(IP_B, port_B, filename, out_dir)
                bytes_B += size
                success_B += 1
            except Exception as e:
                print(f"[ERROR] B {filename}: {e}")
            current += 1
    #Υπολογίζουμε συνολικό χρόνο και τον αποθηκεύουμε σε CSV για μελλοντική ανάλυση
    end = time.time()
    total_time = end - start

    total_bytes = bytes_A + bytes_B
    throughput_mbps = (total_bytes * 8) / (total_time * 1_000_000) if total_time > 0 else 0.0

    print("\nDone!")
    print(f"Total time: {total_time:.3f} seconds")
    print(f"Total bytes: {total_bytes:,}")
    print(f"Estimated throughput: {throughput_mbps:.3f} Mbps")
    print(f"Success A: {success_A}, Success B: {success_B}")

    # Log automatically (append to a master CSV)
    row = {
        "timestamp": time.time(),
        "n_A": n_A,
        "n_B": n_B,
        "IP_A": IP_A,
        "IP_B": IP_B,
        "port_A": port_A,
        "port_B": port_B,
        "total_time": total_time,
        "total_bytes": total_bytes,
        "throughput_mbps": throughput_mbps,
        "success_A": success_A,
        "success_B": success_B,
        "bytes_A": bytes_A,
        "bytes_B": bytes_B
    }
    append_result_row(row)

    # produce aggregated table + bar chart from all runs
    plot_aggregate()


if __name__ == "__main__":
    main()