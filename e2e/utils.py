import os
import time
import random
import string
import yaml


def safe_open(filepath, mode='r'):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    return open(filepath, mode)

def unmarshal_yaml(yaml_file, replacements={}):
    with safe_open(yaml_file) as file:
        contents = file.read()

    for r_key, r_value in replacements.items():
        contents = contents.replace(f"${{{r_key}}}", r_value)
    
    return yaml.safe_load(contents)

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