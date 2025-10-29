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
PORT = 65080
TIMEOUT = 10

GFD_HOST = "127.0.0.1" #change to server ip
GFD_PORT = 65084

def main():
    data = ""
    parser = argparse.ArgumentParser(description="Heartbeat")
    parser.add_argument("-f", "--freq", type=int, default=10)
    parser.add_argument("-t", "--timeout", type=int, default=5)
    parser.add_argument("-i", "--id", type=int, default=1)
    parser.add_argument("--gfd_host", type=str, default=GFD_HOST)
    parser.add_argument("--gfd_port", type=int, default=GFD_PORT)

    args = parser.parse_args()
    heartbeat_interval = args.freq
    global id
    id = args.id
    TIMEOUT = args.timeout

    # connecting to gfd

    gfd_connected = False
    gfd_sock = None
    # Try connecting to GFD, but do not crash if unavailable
    try:
        gfd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        gfd_sock.settimeout(TIMEOUT)
        gfd_sock.connect((args.gfd_host, args.gfd_port))
        gfd_connected = True
        print(f"[{ts()}] LFD{id}: connected to GFD at {args.gfd_host}:{args.gfd_port}")
    except Exception as e:
        print(f"{YELLOW}[{ts()}] LFD{id}: GFD not available yet ({e}); will retry...{RESET}")
    # gfd, gfd_connected = connection(host=GFD_HOST, port=GFD_PORT)

    s, connected = connection()
    # try connecting to server, but do not crash if unavailable
    try:
        s, connected = connection(timeout=TIMEOUT)
    except Exception as e:
        print(f"{YELLOW}[{ts()}] LFD{id}: Server not available yet ({e}); will retry...{RESET}")
        s = None
        connected = False
    first_ack_sent = False
    first_connect = 1

    while True:        
        if gfd_connected: #heartbeats for the gfd
            if first_connect:
                first_connect = 0
                gfd_sock.sendall(f"LFD{id}: Connected \n".encode())
            else:
                try:
                    gfd_sock.sendall(f"LFD{id}: Heartbeat \n".encode())
                    gfd_sock.settimeout(TIMEOUT)
                    print(f"Sending heartbeat at {int(time.time())}")
                    try:
                        resp = gfd_sock.recv(3).decode()
                        if resp == "ACK":
                            print(f"{BLUE}[{ts()}] LFD{id}: ACK received from GFD{RESET}")


                    except socket.timeout:
                        print(f"{RED}[{ts()}] LFD{id}: No ACK (timeout={TIMEOUT}s) GFD may have failed{RESET}")
                        connected = False
                        gfd_sock.close()
                except socket.timeout:
                    print("Timeout exceeded, GFD failed")
                except socket.error as e:
                    print(f"Error sending heartbeat: {e}")
                    print(f"{RED}[{ts()}] LFD{id}: GFD died")
                    gfd_connected = False
                    gfd_sock.close()
                
        print(connected)
        if connected: #heartbeats for the server
            try: 
                s.sendall("Heartbeat".encode())
                print(f"Sending heartbeat at {int(time.time())}")
                # ADDITION: LFD (inside heartbeat loop)
                print(f"{GREEN}[{ts()}] LFD{id}: sending heartbeat to S{id}{RESET}")


                # ADDITION: wait briefly for ACK to confirm server alive
                s.settimeout(TIMEOUT)
                try:
                    resp = s.recv(3).decode()
                    if resp == "ACK":
                        print(f"{BLUE}[{ts()}] LFD{id}: ACK received from server{RESET}")


                except socket.timeout:
                    print(f"{RED}[{ts()}] LFD{id}: No ACK (timeout={TIMEOUT}s) server may have failed{RESET}")
                    connected = False
                    s.close()

            except socket.timeout:
                print("Timeout exceeded, server failed")
            except socket.error as e:
                print(f"Error sending heartbeat")
                print(f"{RED}[{ts()}] LFD{id}: Server {id} died")
                connected = False
                s.close()
                gfd_sock.sendall(f"LFD{id}: Server Disconnected".encode())
                # send "remove replica" message to gfd

        else:
            try:
                print(f"Trying to reconnect")
                # ADDITION: colorize reconnect attempts
                print(f"{YELLOW}[{ts()}] LFD{id}: Attempting reconnect to {HOST}:{PORT+id}{RESET}")
                s, connected = connection()
                if connected:
                    print(f"Connected to server at", HOST)
                    first_connect = 1
                    gfd_sock.sendall(f"LFD{id}: Server Connected".encode())
            except socket.error as e:
                pass
        time.sleep(heartbeat_interval)
    print(f"Received {data!r}")

def connection(host=HOST, port=PORT, timeout=TIMEOUT):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("port:", PORT+id)
        s.connect((HOST, PORT+id))
        s.settimeout(TIMEOUT) 
        # print(f"Connected to server at", HOST)
        connected = True
    except Exception as e:
        print(f"Cannot connect to the server")
        connected = False
    return s, connected


main()