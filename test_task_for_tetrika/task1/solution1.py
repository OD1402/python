import inspect

def strict(func):
    sig = inspect.signature(func)
    annotations = func.__annotations__
    # annotations = {
    #     name: param.annotation
    #     for name, param in sig.parameters.items()
    #     if param.annotation is not inspect._empty
    # }

    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)

        for name, value in bound.arguments.items():
            if name in annotations:
                expected_type = annotations[name]
                existing_type = type(value)

                if not isinstance(value, expected_type):
                    raise TypeError(
                        f"Аргумент '{name}' должен быть {expected_type.__name__}, а передан {existing_type.__name__} \n"
                        f"value: {value} \n"
                        f"expected_type: {expected_type.__name__} \n"
                        f"existing_type: {existing_type.__name__} \n"
                    )
        return func(*args, **kwargs)

    return wrapper


@strict
def sum_two(a: int, b: int) -> int:
    return a + b


# print(sum_two(1))  # TypeError
# print(sum_two(1, 2))  # 3
# print(sum_two(1, 2.4))  # TypeError
