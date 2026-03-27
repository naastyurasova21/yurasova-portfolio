import os
import time
import select


class ServerApp():
    def __init__(self):
        self.mode = 'WAITING_REQUEST'
        self.tx_pipe = "/tmp/pong_pipe"
        self.rx_pipe = "/tmp/ping_pipe"
        self.msg_buf = None
        self.tx_desc = None
        self.rx_desc = None

    def setup_pipes(self):
        try:
            os.unlink(self.tx_pipe)
            os.unlink(self.rx_pipe)
        except FileNotFoundError:
            pass
        try:
            os.mkfifo(self.tx_pipe, 0o666)
            os.mkfifo(self.rx_pipe, 0o666)
            print('Pipes established')
            print('Awaiting client link...')
            return True
        except PermissionError as pe:
            print(f"Access denied: {pe}")
            return False
        except Exception as ex:
            print(f"Pipe setup failed: {ex}")
            return False

    def close_all(self):
        descs = [self.rx_desc, self.tx_desc]
        for d in descs:
            if d:
                os.close(d)
        pipes = [self.tx_pipe, self.rx_pipe]
        for p in pipes:
            os.unlink(p)

    def state_one(self):
        if self.rx_desc is None:
            try:
                self.rx_desc = os.open(self.rx_pipe, os.O_RDONLY | os.O_NONBLOCK)
                self.tx_desc = os.open(self.tx_pipe, os.O_WRONLY)
                print('Linked with client')
            except PermissionError:
                print("Pipe access denied")
                return False
            except FileNotFoundError:
                print("Pipes missing")
                return False
        
        print(f'Server: phase 1 ({self.mode})')
        
        r, _, _ = select.select([self.rx_desc], [], [], None)
        
        if r:
            raw = os.read(self.rx_desc, 1024)
            self.mode = 'CHECKING_REQUEST'
            self.msg_buf = raw.decode('utf-8').strip()
            return True

    def state_two(self):
        print(f'Server: phase 2 ({self.mode})')
        if self.msg_buf:
            print(f"Data: {self.msg_buf}")
        else:
            print("Empty request")
        
        if self.msg_buf == 'close':
            print("Shutdown ")
            return False
        
        self.mode = 'SENDING_RESPONSE'
        return True

    def state_three(self):
        print(f'Server: phase 3 ({self.mode})')
        resp_map = {
            'PING': 'PONG',
            '': 'Error: Empty request'
        }
        
        cmd = self.msg_buf.upper() if self.msg_buf else ''
        reply = resp_map.get(cmd, 'Error command')
        data_out = (reply + '\n').encode()
        sent = os.write(self.tx_desc, data_out)
        print("Reply dispatched")
        self.mode = 'WAITING_REQUEST'
        
        return True

    def execute_server(self):
        if not self.setup_pipes():
            print("Initialization failed")
            return
        
        state_actions = {
            'WAITING_REQUEST': self.state_one,
            'CHECKING_REQUEST': self.state_two,
            'SENDING_RESPONSE': self.state_three
        }
        
        try:
            while True:
                action = state_actions.get(self.mode)
                if action:
                    if not action():
                        if self.mode == 'CHECKING_REQUEST' and self.msg_buf == 'close':
                            break
                        print("Restarting connection...")
                        self.close_all()
                        time.sleep(1)
                        if not self.setup_pipes():
                            break
                        self.mode = 'WAITING_REQUEST'
                else:
                    print(f"Unknown mode: {self.mode}")
                    break
                
                time.sleep(0.05)
                
        except Exception as ex:
            print(f"Unexpected: {ex}")
        finally:
            self.close_all()


def server():
    app = ServerApp()
    app.execute_server()


if __name__ == "__main__":
    server()
