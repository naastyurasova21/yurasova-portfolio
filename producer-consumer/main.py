import threading
import random
import time
import argparse
import json
import signal
from queue import Queue, Full, Empty
from datetime import datetime

task_queue = Queue(maxsize=10)
reslock = threading.Lock()
res = []
flag = threading.Event()
print_lock = threading.Lock()
start_time = None


class TextTaski:
    def __init__(self, task_id, text, oper):
        self.task_id = task_id
        self.text = text
        self.oper = oper

    def __str__(self):
        return f'Task {self.task_id}: {self.oper}'


class TextRes:
    def __init__(self, task_id, oper, res_data):
        self.task_id = task_id
        self.oper = oper
        self.res_data = res_data
        self.times = datetime.now().strftime("%H:%M:%S")

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "oper": self.oper,
            "result": self.res_data,
            "time": self.times
        }

    def __str__(self):
        return f'{self.times} Task {self.task_id} - {self.oper}: {self.res_data}'


class Producer(threading.Thread):
    def __init__(self, producer_id, counter):
        super().__init__()
        self.producer_id = producer_id
        self.counter = counter
        self.task_sozd = 0
        self.daemon = True

    def run(self):
        with print_lock:
            print(f'Producer {self.producer_id} started, will create {self.counter} tasks')

        try:
            with open('texts.txt', 'r', encoding='utf-8') as file:
                texts = [line.strip() for line in file if line.strip()]
            if not texts:
                with print_lock:
                    print(f'Producer {self.producer_id}: texts.txt is empty')
                return
        except FileNotFoundError:
            with print_lock:
                print(f'Producer {self.producer_id}: texts.txt not found')
            return

        operations = ['cwords', 'cletters', 'reverse']
        for i in range(self.counter):
            if flag.is_set():
                with print_lock:
                    print(f'Producer {self.producer_id} received shutdown signal')
                break
            task_id = self.producer_id * 1000 + i
            text = random.choice(texts)
            oper = random.choice(operations)
            task = TextTaski(task_id, text, oper)
            try:
                task_queue.put(task, timeout=1)
                self.task_sozd += 1
                with print_lock:
                    print(f'Producer {self.producer_id} created {task}')
                time.sleep(random.uniform(0.3, 0.8))
            except Full:
                with print_lock:
                    print(f'Producer {self.producer_id}: queue is full')
                time.sleep(1)
        with print_lock:
            print(f'Producer {self.producer_id} finished, created {self.task_sozd} tasks')


class Consumer(threading.Thread):
    def __init__(self, consumer_id):
        super().__init__()
        self.consumer_id = consumer_id
        self.obtask_count = 0
        self.daemon = True

    def run(self):
        with print_lock:
            print(f'Consumer {self.consumer_id} started')

        while not flag.is_set() or not task_queue.empty():
            try:
                task = task_queue.get(timeout=1)
                result_data = self.ob_task(task)
                result = TextRes(task.task_id, task.oper, result_data)
                with reslock:
                    res.append(result)
                self.obtask_count += 1
                with print_lock:
                    print(f'Consumer {self.consumer_id} completed Task #{task.task_id}')
                time.sleep(random.uniform(0.5, 1.5))
            except Empty:
                if not flag.is_set():
                    continue
                else:
                    break
        with print_lock:
            print(f'Consumer {self.consumer_id} finished, processed {self.obtask_count} tasks')

    def ob_task(self, task):
        text = task.text
        if task.oper == 'cwords':
            words = text.split()
            return f'Words: {len(words)}'
        elif task.oper == 'cletters':
            letters = [c for c in text if c.isalpha()]
            return f'Letters: {len(letters)}'
        elif task.oper == 'reverse':
            return f'Reversed: {text[::-1]}'
        else:
            return "Unknown operation"


def save_results():
    """Save results to JSON file"""
    with reslock:
        results_list = [r.to_dict() for r in res]
    try:
        with open('results.json', 'w', encoding='utf-8') as f:
            json.dump(results_list, f, ensure_ascii=False, indent=2)
        with print_lock:
            print(f'\nResults saved to results.json ({len(results_list)} records)')
    except Exception as e:
        with print_lock:
            print(f'\nError saving results: {e}')


def signal_handler(signum, frame):
    """Ctrl+C handler for graceful shutdown"""
    with print_lock:
        print('\n\nShutdown signal received (Ctrl+C)')
        print('Shutting down... Waiting for current tasks to complete')
    flag.set()


def main():
    global start_time

    parser = argparse.ArgumentParser(description='Producer-Consumer text processing system')
    parser.add_argument('--producers', type=int, default=2, help='Number of producers (default: 2)')
    parser.add_argument('--consumers', type=int, default=3, help='Number of consumers (default: 3)')
    parser.add_argument('--tasks', type=int, default=8, help='Tasks per producer (default: 8)')
    parser.add_argument('--no-save', action='store_true', help='Do not save results to file')

    args = parser.parse_args()

    num_producers = args.producers
    num_consumers = args.consumers
    tasks_per_producer = args.tasks

    with print_lock:
        print(f'Starting with: producers={num_producers}, consumers={num_consumers}, tasks={tasks_per_producer}')

    signal.signal(signal.SIGINT, signal_handler)

    start_time = time.time()

    producers = []
    consumers = []

    for i in range(num_consumers):
        consumer = Consumer(i + 1)
        consumers.append(consumer)
        consumer.start()

    for i in range(num_producers):
        producer = Producer(i + 1, tasks_per_producer)
        producers.append(producer)
        producer.start()

    try:
        for producer in producers:
            producer.join()

        flag.set()

        for consumer in consumers:
            consumer.join(timeout=5)

        with print_lock:
            print('\nAll threads finished')

        end_time = time.time()
        total_time = end_time - start_time
        with print_lock:
            print(f'Execution time: {total_time:.2f} seconds')

        if not args.no_save and len(res) > 0:
            save_results()

    except KeyboardInterrupt:
        flag.set()
        with print_lock:
            print('\nWaiting for threads to finish...')

        for consumer in consumers:
            consumer.join(timeout=3)
        for producer in producers:
            producer.join(timeout=1)

        end_time = time.time()
        total_time = end_time - start_time
        with print_lock:
            print(f'Execution time (interrupted): {total_time:.2f} seconds')

        if not args.no_save and len(res) > 0:
            save_results()

        with print_lock:
            print('Program finished')


if __name__ == "__main__":
    main()