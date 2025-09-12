import socket
import argparse

HOST = "172.26.42.163" #change to server ip
PORT = 65083

def main():
    parser = argparse.ArgumentParser(description="Client ID")
    parser.add_argument("-c", "--client", type=int, default=0)
    args = parser.parse_args()

    client_id = args.client
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print(f"Client {client_id} connected to server")

        while True:
            msg = input(">>> ")
            if msg.lower() == "quit":
                break
            
            msg = f"Client {client_id}: {msg}"
            s.sendall(msg.encode())
            print("Message sent")
            data = s.recv(1024).decode()
            print(f"Server received {data!r}")

main()