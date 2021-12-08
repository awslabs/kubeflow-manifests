import os
import time
import random
import string


def safe_open(filepath, mode='r'):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    return open(filepath, mode)


def wait_for(callback, timeout=300, interval=10):
    start = time.time()
    while True:
        try:
            return callback()
        except Exception as e:
            if time.time() - start >= timeout:
                raise e
            time.sleep(interval)

def rand_name(prefix):
    suffix = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
    return prefix + suffix