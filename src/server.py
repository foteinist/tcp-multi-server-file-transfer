import socket #δημιουργία TCP sockets
import struct #χρησιμοποιείται για να στείλουμε/διαβάσουμε το μέγεθος του αρχείου σε 8 bytes
import threading #για να χειριστούμε κάθε σύνδεση σε ξεχωριστό thread (πολλαπλές συνδέσεις ταυτόχρονα)
import os #έλεγχοι αρχείων και μέγεθος
import sys #διαβάζει το όρισμα port από τη γραμμή εντολών

#conn: socket αντικείμενο που αντιπροσωπεύει τη σύνδεση με τον client
#addr: διεύθυνση του client (IP,port)
#Ο κώδικας διαβάζει bytes από το socket σε κομμάτια των 1024 bytes μέχρι να βρει το newline \n. Αυτό εξασφαλίζει ότι διαβάζουμε ολόκληρη την εντολή (π.χ. GET_FILE s001.m4s\n)
#Αν recv επιστρέψει κενά bytes (if not chunk) σημαίνει ότι ο client έκλεισε τη σύνδεση — τερματίζουμε την επεξεργασία

def handle_client(conn, addr): #εξυπηρετεί μία σύνδεση, δηλαδή έναν client που συνδέθηκε
    print(f"[+] Connection from {addr}")
    try:
        #Read request until newline
        request = b""
        while b"\n" not in request:
            chunk = conn.recv(1024)
            if not chunk:
                return
            request += chunk

        request = request.decode().strip() #Μετατρέπουμε από bytes σε string (.decode()), αφαιρούμε περιττά whitespaces με strip()

        if request.startswith("GET_FILE"): #Ελέγχουμε αν το αίτημα ξεκινάει με GET_FILE. Αν ναι, κάνουμε split και παίρνουμε το όνομα αρχείου (δεύτερο πεδίο)
            _, filename = request.split()

            if not os.path.isfile(filename): #Ελέγχουμε αν το αρχείο υπάρχει στον τοπικό δίσκο
                #Send size = 0 (file not found)
                conn.sendall(struct.pack("!Q", 0)) #Αν δεν υπάρχει, στέλνουμε 8 bytes που αντιπροσωπεύουν την ακέραια τιμή 0: struct.pack("!Q", 0)
                #! = network byte order (big-endian)
                #Q = unsigned long long (8 bytes)
                #Ο client, όταν λάβει μέγεθος 0, ξέρει ότι το αρχείο δεν υπάρχει
                print(f"[!] File not found: {filename}")
                return
            #Παίρνουμε το μέγεθος του αρχείου σε bytes και το στέλνουμε πρώτα (ως 8-byte unsigned integer)
            #Αυτό επιτρέπει στον client να ξέρει πόσα bytes θα περιμένει
            size = os.path.getsize(filename)

            #Send file size (8 bytes)
            conn.sendall(struct.pack("!Q", size))

            #Send file data in chunks
            with open(filename, "rb") as f: #Ανοίγουμε το αρχείο σε δυαδική ανάγνωση ("rb")
                #Διαβάζουμε και στέλνουμε σε chunks των 65536 bytes (64 KB) μέχρι να τελειώσει το αρχείο. Αυτό είναι πιο αποδοτικό και ασφαλές για μεγάλα αρχεία σε σχέση με το να διαβάζαμε όλο το αρχείο σε μνήμη
                while True:
                    data = f.read(65536)
                    if not data:
                        break
                    conn.sendall(data)

            print(f"[OK] Sent {filename} ({size} bytes) to {addr}")

    except Exception as e:
        print(f"[ERROR] {addr}: {e}") #Εάν γίνει οποιοδήποτε σφάλμα το τυπώνουμε

    finally:
        conn.close() #Στο finally κλείνουμε πάντα το socket conn.close() — αυτό εξασφαλίζει ότι δεν μένουν ανοικτές συνδέσεις

#Αυτή ξεκινάει τον TCP server και δέχεται συνεχώς συνδέσεις
#socket(AF_INET, SOCK_STREAM): δημιουργεί TCP socket IPv4
#bind(("0.0.0.0", port)): δένει το socket σε όλες τις διεπαφές της μηχανής (0.0.0.0) στo συγκεκριμένo port. Αυτό σημαίνει ότι ο server θα ακούει σε όλες τις IP διευθύνσεις του μηχανήματος.
#listen(5): βάζει το socket σε κατάσταση ακρόασης — 5 είναι το backlog (πόσες αναμονές συνδέσεων να κρατάει το OS)

def start_server(port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", port))
    server_socket.listen(5)
    print(f"Server listening on port {port}...")

    while True:
        conn, addr = server_socket.accept() #accept() μπλοκάρει μέχρι να έρθει σύνδεση. Επιστρέφει ένα νέο socket conn για τη συγκεκριμένη σύνδεση και την διεύθυνση addr
        #Για κάθε νέα σύνδεση δημιουργούμε ένα νέο thread που τρέχει handle_client(conn, addr). Το thread είναι daemon=True ώστε αν τερματίσει το κύριο πρόγραμμα να μην εμποδίζει shutdown
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

#Ελέγχουμε τα arguments. Αναμένουμε 1 όρισμα: το port
#Αν δεν δοθεί σωστά, ξεκινάμε το server με το δοθέν port
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python server.py <port>")
        sys.exit(1)
    start_server(int(sys.argv[1]))
