# Named Pipes IPC — Client-Server Communication via FIFO

## Stack
- **Language:** Python 3.10+
- **IPC:** Named Pipes (FIFO)
- **I/O Multiplexing:** select()
- **Pattern:** Finite State Machine (FSM)

## Description
A client-server application demonstrating inter-process communication (IPC) using named pipes (FIFO) in Unix-like systems. The server creates two named pipes and waits for client connections. The client connects, sends commands, and receives responses. The application uses `select()` for non-blocking I/O multiplexing and implements a finite state machine for managing connection states.

### How It Works
- **Server** creates two FIFOs: `/tmp/ping_pipe` (client → server) and `/tmp/pong_pipe` (server → client)
- **Client** connects to both pipes and sends commands
- **Server** processes commands and sends responses
- Communication is text-based with newline termination

### Supported Commands
| Command | Response |
|---------|----------|
| `PING` | `PONG` |
| `close` | Terminates connection |
| *(empty)* | `Error: Empty request` |
| *(other)* | `Error command` |

### Key Features
- Non-blocking I/O with `select()`
- Finite State Machine for state management
- Graceful connection handling with retry logic
- Timeout handling for responses
- Resource cleanup (file descriptors, pipe files)

### Future Improvments
- Add support for multiple clients (using select() with multiple file descriptors)
- Implement request queuing for concurrent processing
- Add logging module instead of print statements
- Add unit tests for state transitions

## How to Run

### First terminal

```bash
python server.py
```

### Second terminal
```bash
python client.py
```