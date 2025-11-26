from functools import reduce


def compose(*funcs):
    """
    Composes functions right to left.
    compose(f, g)(x) = f(g(x))
    """
    return lambda x: reduce(lambda v, f: f(v), reversed(funcs), x)


def pipe(x, *funcs):
    """
    Pipes value x through functions left to right.
    pipe(x, f, g) = g(f(x))
    """
    return reduce(lambda v, f: f(v), funcs, x)
