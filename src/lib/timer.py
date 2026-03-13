import time


def timer(logger=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            t1 = time.perf_counter()
            result = func(*args, **kwargs)
            t2 = time.perf_counter()
            execution_time = t2 - t1
            if logger:
                logger.info(
                    f"Execution time of '{func.__name__}': {execution_time:.2f} seconds"
                )
            else:
                print(
                    f"Execution time of '{func.__name__}': {execution_time:.2f} seconds."
                )
            return result

        return wrapper

    return decorator
