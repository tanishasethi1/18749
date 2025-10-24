import socket
import argparse



# ADDITION: for timestamps and colored console output
from datetime import datetime
BLUE = "\033[94m"    # client-server send/receive
CYAN = "\033[96m"    # duplicate detection (for later)
RESET = "\033[0m"

def ts():
    return datetime.now().strftime("%H:%M:%S")

# 
HOST = "127.0.0.1" #change to server ip
PORT = 65080

SERVER1_HOST = "127.0.0.1"
SERVER1_PORT = 65081

SERVER2_HOST = "127.0.0.1"
SERVER2_PORT = 65082

SERVER3_HOST = "127.0.0.1"
SERVER3_PORT = 65083
    

def main():
    # create TCP socket
    parser = argparse.ArgumentParser(description="Client")
    parser.add_argument("-i", "--id", type=int, default=1)
    # parser.add_argument("-p", "--port", type=int, default=1)

    args = parser.parse_args()
    global client_id
    client_id = args.id
    # ADDITION: simple request counter
    req_num = 0

    servers = [(SERVER1_HOST, SERVER1_PORT), (SERVER2_HOST, SERVER2_PORT), (SERVER3_HOST, SERVER3_PORT)]
    connected_sockets = []
    
    # connections to all 3 servers
    for i in range(3):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            s.connect((servers[i][0], servers[i][1]))
            print(f"Client {client_id} connected to server {i+1} at {servers[i][0]}:{servers[i][1]}")
            connected_sockets.append(s)
        except Exception as e:
            print(f"Server {i+1} not available")

    # message sending (continuous loop)
    while True:
        message = f"C{client_id}: request{req_num} --> Hello!"

        # sending to the three servers...?
        for i in range(3):
            curr_socket = connected_sockets[i]
            try:
                curr_socket.sendall(message.encode())
                print(f"{BLUE}[{ts()}] Client {client_id}: Sending {message}{RESET}")
            except Exception as e:
                print(f"Failed to send message to server {i+1}")

        # receive ACKs from three servers... ;-;
        for i in range(3):
            curr_socket = connected_sockets[i]
            

    # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #     s.connect((HOST, PORT))
    #     print(f"Client {client_id} connected to server")

    #     while True:
    #         msg = input(">>> ")
    #         if msg.lower() == "quit":
    #             break

    #         # ADDITION: increment request number
    #         req_num += 1
    #         formatted = f"<C{client_id}, req{req_num}>: {msg}"
    #         print(f"{BLUE}[{ts()}] Client 1: Sending {formatted}{RESET}")
            
    #         msg = f"Client {client_id}: {msg}"
    #         s.sendall(msg.encode())
    #         print("Message sent")
    #         data = s.recv(1024).decode()

    #         # ADDITION: timestamp the received reply
    #         print(f"{BLUE}[{ts()}] Client 1: Received reply: {data!r}{RESET}")
            
    #         print(f"Server received {data!r}")

main()