"""
Generic helper methods module
"""

import os
import time
import random
import string
import yaml


def safe_open(filepath, mode='r'):
    """
    Creates a directory if one does not exist when opening a file.
    """

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    return open(filepath, mode)

def unmarshal_yaml(yaml_file, replacements={}):
    """
    Unmarshals yaml into a python object.

    `replacements` allow substituting values in the yaml file.

    Ex:

        replacements = {"NAMESPACE", "kubeflow"}

        metadata:
            - name: ...
            - namespace: ${NAMESPACE}

        will become

        metadata:
            - name: ...
            - namespace: kubeflow
    """

    with open(yaml_file) as file:
        contents = file.read()

    for r_key, r_value in replacements.items():
        contents = contents.replace(f"${{{r_key}}}", r_value)
    
    return yaml.safe_load(contents)

def wait_for(callback, timeout=300, interval=10):
    """
    Provide a function with no arguments as a callback.

    Repeatedly calls the callback on an interval until the timeout duration
    or until the callback returns without raising an exception.

    If the timeout duration is exceeded raises the last raised exception
    """

    start = time.time()
    while True:
        try:
            return callback()
        except Exception as e:
            if time.time() - start >= timeout:
                raise e
            time.sleep(interval)

def rand_name(prefix):
    """
    Returns a random string of 10 ascii lowercase characters appended to the prefix
    """
    suffix = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
    return prefix + suffix