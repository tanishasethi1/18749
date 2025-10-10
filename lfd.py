import socket
import time
import argparse

from datetime import datetime
GREEN = "\033[92m"   # successful heartbeat
RED = "\033[91m"     # failure or timeout
YELLOW = "\033[93m"  # reconnect attempt
BLUE = "\033[94m"    # server ack
RESET = "\033[0m"

def ts():
    return datetime.now().strftime("%H:%M:%S")

HOST = "127.0.0.1" #change to server ip
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
    first_ack_sent = False

    while True:
        print(connected)
        if connected:
            try: 
                s.sendall("Heartbeat".encode())
                print(f"Sending heartbeat at {int(time.time())}")
                # ADDITION: LFD (inside heartbeat loop)
                print(f"{GREEN}[{ts()}] LFD1: sending heartbeat to S1{RESET}")


                # ADDITION: wait briefly for ACK to confirm server alive
                s.settimeout(TIMEOUT)
                try:
                    resp = s.recv(3).decode()
                    if resp == "ACK":
                        print(f"{BLUE}[{ts()}] LFD 1: ACK received from server{RESET}")


                except socket.timeout:
                    print(f"{RED}[{ts()}] LFD 1: No ACK (timeout={TIMEOUT}s) server may have failed{RESET}")
                    connected = False
                    s.close()

            except socket.timeout:
                print("Timeout exceeded, server failed")
            except socket.error as e:
                print(f"Error sending heartbeat: {e}")
                print(f"{RED}[{ts()}] LFD 1: Server 1 died")
                connected = False
                s.close()

        else:
            try:
                print(f"Trying to reconnect")
                # ADDITION: colorize reconnect attempts
                print(f"{YELLOW}[{ts()}] LFD 1: Attempting reconnect to {HOST}:{PORT}{RESET}")
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