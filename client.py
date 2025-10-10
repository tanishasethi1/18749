import socket
import argparse



# ADDITION: for timestamps and colored console output
from datetime import datetime
BLUE = "\033[94m"    # client-server send/receive
CYAN = "\033[96m"    # duplicate detection (for later)
RESET = "\033[0m"

def ts():
    return datetime.now().strftime("%H:%M:%S")
HOST = "127.0.0.1" #change to server ip
PORT = 65083
    

def main():
    parser = argparse.ArgumentParser(description="Client ID")
    parser.add_argument("-c", "--client", type=int, default=0)
    args = parser.parse_args()

    client_id = args.client
    # ADDITION: simple request counter
    req_num = 0

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print(f"Client {client_id} connected to server")

        while True:
            msg = input(">>> ")
            if msg.lower() == "quit":
                break

            # ADDITION: increment request number
            req_num += 1
            formatted = f"<C{client_id}, req{req_num}>: {msg}"
            print(f"{BLUE}[{ts()}] Client 1: Sending {formatted}{RESET}")
            
            msg = f"Client {client_id}: {msg}"
            s.sendall(msg.encode())
            print("Message sent")
            data = s.recv(1024).decode()

            # ADDITION: timestamp the received reply
            print(f"{BLUE}[{ts()}] Client 1: Received reply: {data!r}{RESET}")
            
            print(f"Server received {data!r}")

main()