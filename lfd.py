import socket
import time
import argparse

HOST = "172.26.0.108" #change to server ip
PORT = 65083
TIMEOUT = 10

def main():
    data = ""
    parser = argparse.ArgumentParser(description="Heartbeat")
    parser.add_argument("-f", "--freq", type=int, default=10)
    parser.add_argument("-t", "--timeout", type=int, default=5)

    args = parser.parse_args()
    heartbeat_interval = args.freq
    TIMEOUT = args.timeout
    s, connected = connection()
    while True:
        print(connected)
        if connected:
            try: 
                s.sendall("Heartbeat".encode())
                print(f"Sending heartbeat at {int(time.time())}")
            except socket.timeout:
                print("Timeout exceeded, server failed")
            except socket.error as e:
                print(f"Error sending heartbeat: {e}")
                print(f"Server died")
                connected = False
                s.close()
        else:
            try:
                print(f"Trying to reconnect")
                s, connected = connection()
                print(f"Connected to server at", HOST)
            except socket.error as e:
                pass
        time.sleep(heartbeat_interval)

    print(f"Received {data!r}")

def connection():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.settimeout(TIMEOUT) 
    print(f"Connected to server at", HOST)
    connected = True
    return s, connected


main()