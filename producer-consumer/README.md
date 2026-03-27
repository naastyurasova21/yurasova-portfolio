# Producer-Consumer — Multithreaded Text Processing System

## Stack
- **Language:** Python 3.10+
- **Libraries:** threading, queue, argparse, json, signal, datetime

## Description
A classic Producer-Consumer pattern implementation for parallel text processing.

**Producer** — reads lines from `texts.txt` and creates tasks of three types:
- `cwords` — count words in a string
- `cletters` — count letters in a string
- `reverse` — reverse the string

**Consumer** — retrieves tasks from the queue, processes them, and stores results.

### Key Features
- Bounded queue (maxsize = 10)
- Thread-safe synchronization using `Lock`
- Graceful shutdown on `Ctrl+C` — waits for current tasks to complete and saves results
- Results saved to `results.json`
- Command-line arguments for configuration
- Exception handling for `Full` and `Empty` queue states

## How to Run

```bash
python main.py
```
