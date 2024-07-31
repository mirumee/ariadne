import time


def wait_for_condition(condition_func, timeout=5, poll_interval=0.1):
    """
    This function is particularly useful in scenarios where asynchronous operations
    are involved. For instance, in a WebSocket-based system, certain events or
    state changes, like setting a flag in a callback, may not occur instantly.
    The wait_for_condition function ensures that the test waits long enough for
    these asynchronous events to complete, preventing race conditions or false
    negatives in test outcomes.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(poll_interval)
    return False
