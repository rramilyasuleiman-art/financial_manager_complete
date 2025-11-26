from typing import Callable, Generic, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")
R = TypeVar("R")


class Maybe(Generic[T]):
    def __init__(self, value: Union[T, None]):
        self._value = value

    @staticmethod
    def just(value: T) -> "Maybe[T]":
        return Maybe(value)

    @staticmethod
    def nothing() -> "Maybe[T]":
        return Maybe(None)

    def is_present(self) -> bool:
        return self._value is not None

    def map(self, func: Callable[[T], R]) -> "Maybe[R]":
        if self._value is None:
            return Maybe.nothing()
        return Maybe.just(func(self._value))

    def bind(self, func: Callable[[T], "Maybe[R]"]) -> "Maybe[R]":
        if self._value is None:
            return Maybe.nothing()
        return func(self._value)

    def get_or_else(self, default: T) -> T:
        return self._value if self._value is not None else default

    def __repr__(self):
        return f"Maybe({self._value})"

    def __eq__(self, other):
        return isinstance(other, Maybe) and self._value == other._value


class Either(Generic[E, T]):
    def __init__(self, value: Union[E, T], is_right: bool):
        self._value = value
        self._is_right = is_right

    @staticmethod
    def left(error: E) -> "Either[E, T]":
        return Either(error, is_right=False)

    @staticmethod
    def right(value: T) -> "Either[E, T]":
        return Either(value, is_right=True)

    def is_right(self) -> bool:
        return self._is_right

    def is_left(self) -> bool:
        return not self._is_right

    def map(self, func: Callable[[T], R]) -> "Either[E, R]":
        if self.is_left():
            return Either(self._value, is_right=False)
        return Either.right(func(self._value))

    def bind(self, func: Callable[[T], "Either[E, R]"]) -> "Either[E, R]":
        if self.is_left():
            return Either(self._value, is_right=False)
        return func(self._value)

    def get_or_else(self, default: T) -> T:
        return self._value if self.is_right() else default

    def unwrap(self) -> Union[E, T]:
        return self._value

    def __repr__(self):
        return f"Right({self._value})" if self._is_right else f"Left({self._value})"

    def __eq__(self, other):
        return (
            isinstance(other, Either)
            and self._value == other._value
            and self._is_right == other._is_right
        )
