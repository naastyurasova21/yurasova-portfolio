import os
import time
import select


class ClientApp():
    def __init__(self):
        self.current_state = 'CREATING_REQUEST'
        self.user_input = None
        
        self.send_path = "/tmp/ping_pipe"
        self.recv_path = "/tmp/pong_pipe"
        self.send_fd = None
        self.recv_fd = None
        
        print("Client Application")

    def release_resources(self):
        for fd in [self.recv_fd, self.send_fd]:
            if fd:
                os.close(fd)

    def connect(self):
        for i in range(1, 4):
            try:
                self.send_fd = os.open(self.send_path, os.O_WRONLY)
                self.recv_fd = os.open(self.recv_path, os.O_RDONLY | os.O_NONBLOCK)
                print(f"[{time.strftime('%H:%M:%S')}] Connection is successful")
                return True
            except FileNotFoundError:
                if i < 3:
                    print(f"[{time.strftime('%H:%M:%S')}] Waiting for server ({i}/3)...")
                    time.sleep(1.5)
                else:
                    print('Server unavailable')
                    return False 
            except PermissionError:
                print(f"[{time.strftime('%H:%M:%S')}] Access denied")
                return False
        return False

    def send_data(self):
        print(f'[{time.strftime("%H:%M:%S")}] Client send phase ({self.current_state})')
        print(f'[{time.strftime("%H:%M:%S")}] Transmitting: {self.user_input}')

        msg_bytes = (self.user_input + '\n').encode()
        written = os.write(self.send_fd, msg_bytes)
        print(f'[{time.strftime("%H:%M:%S")}] Transmission complete')
        self.current_state = 'WAITING_FOR_ANSWER'
        
        return self.user_input != 'close'

    def wait_response(self):
        print(f'[{time.strftime("%H:%M:%S")}] Client wait phase ({self.current_state})')
        print(f'[{time.strftime("%H:%M:%S")}] Awaiting reply...')
        start_time = time.time()

        while time.time() - start_time < 20:
            ready, _, _ = select.select([self.recv_fd], [], [], 0.5)
            if ready:
                self.current_state = "READING_RESPONSE"
                return True
            if time.time() - start_time > 1:
                print("·", end="", flush=True)

        print(f"\n[{time.strftime('%H:%M:%S')}] Response timeout!")
        return False

    def receive_response(self):
        data = os.read(self.recv_fd, 1024)
        response_text = data.decode('utf-8').strip()
        
        print(f'[{time.strftime("%H:%M:%S")}] Client receive phase ({self.current_state})')
        print(f'[{time.strftime("%H:%M:%S")}] Received: {response_text}')
        
        self.current_state = "CREATING_REQUEST"
        self.user_input = None

    def run_client(self):
        print(f"[{time.strftime('%H:%M:%S')}] Client starting...")

        if not self.connect():
            print(f"[{time.strftime('%H:%M:%S')}] Connection failed")
            self.release_resources()
            return

        try:
            while True:
                if self.current_state == "CREATING_REQUEST":
                    if self.user_input is None:
                        cmd = input(f"[{time.strftime('%H:%M:%S')}] Input (or 'close'): ").strip()
                        if cmd:
                            self.user_input = cmd
                    
                    if not self.send_data(): 
                        print(f"[{time.strftime('%H:%M:%S')}] Terminating...")
                        break

                elif self.current_state == "WAITING_FOR_ANSWER":
                    if not self.wait_response(): 
                        print(f"[{time.strftime('%H:%M:%S')}] Connection problem")
                        break

                elif self.current_state == "READING_RESPONSE":
                    self.receive_response()

                time.sleep(0.3)

        finally:
            self.release_resources()
            print(f"[{time.strftime('%H:%M:%S')}] Client stopped")


def client():
    client_app = ClientApp()
    client_app.run_client()


if __name__ == "__main__":
    client()
