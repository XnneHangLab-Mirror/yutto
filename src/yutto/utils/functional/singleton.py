from __future__ import annotations

import warnings
from typing import Any, TypeVar

T = TypeVar("T")


class Singleton(type):
    """单例模式元类

    ### Refs

    - https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python

    ### Examples

    ``` python
    class MyClass(BaseClass, metaclass=Singleton):
        pass

    obj1 = MyClass()
    obj2 = MyClass()
    assert obj1 is obj2
    ```
    """

    _instances: dict[Any, Any] = {}
    _init_args: dict[Any, tuple[tuple[Any, ...], dict[str, Any]]] = {}

    def __call__(cls, *args: Any, **kwargs: Any):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
            cls._init_args[cls] = (args, kwargs)
        elif args or kwargs:
            prev_args, prev_kwargs = cls._init_args[cls]
            if args != prev_args or kwargs != prev_kwargs:
                warnings.warn(
                    f"{cls.__name__} is a Singleton already initialised with "
                    f"args={prev_args!r}, kwargs={prev_kwargs!r}; "
                    f"subsequent args={args!r}, kwargs={kwargs!r} are ignored.",
                    stacklevel=2,
                )
        return cls._instances[cls]
