"""Miscellaneous tools, boilerplate, and shortcuts"""
import inspect
import types
import typing as t
from dataclasses import Field, dataclass, field
from datetime import datetime
from functools import partial

T = t.TypeVar('T')


dclass = partial(dataclass, frozen=True)


def apply(func, args=(), kwargs=None):
    """apply args and kwargs to a function"""
    return func(*args, **kwargs or {})


def notnone(obj):
    """return whether an object is not None"""
    return obj is not None


class StrRepr():
    """mixin which adds a ``__repr__`` based on ``__str__``"""

    def __str__(self):
        return '{0.__class__.__name__} object'.format(self)

    def __repr__(self):
        return '<{0.__class__.__name__}: {0}>'.format(self)


class NO_DEFAULT:
    """sentinel for no default"""


@dclass
class lookup_defaults(t.Callable[[t.Any], T]):
    """wrap a lookup function with a default if lookup fails"""
    lookup: t.Callable[[t.Any], T]
    default: T

    def __call__(self, obj):
        try:
            return self.lookup(obj)
        except LookupError:
            return self.default


def parse_iso8601(dtstring: str) -> datetime:
    """naive parser for ISO8061 datetime strings,

    Parameters
    ----------
    dtstring
        the datetime as string in one of two formats:

        * ``2017-11-20T07:16:29+0000``
        * ``2017-11-20T07:16:29Z``

    """
    return datetime.strptime(
        dtstring,
        '%Y-%m-%dT%H:%M:%SZ' if len(dtstring) == 20 else '%Y-%m-%dT%H:%M:%S%z')


# TODO: types
def genresult(gen, value):
    """retrieve the return value from a generator"""
    try:
        gen.send(value)
    except StopIteration as e:
        return e.value
    else:
        raise TypeError('generator did not return as expected')


def func_to_fields(func: types.FunctionType) -> t.List[Field]:
    """get dataclass fields from a function signature

    Parameters
    ----------
    func
        a python function

    Notes
    -----
    * keyword-only, varargs, and varkeywords are not supported
    """
    spec = inspect.getfullargspec(func)
    defaults = dict(zip(reversed(spec.args), reversed(spec.defaults or ())))
    if spec.kwonlyargs:
        raise TypeError('keyword-only args not supported')
    elif spec.varargs:
        raise TypeError('varargs not supported')
    elif spec.varkw:
        raise TypeError('varkw not supported')
    return [
        (name,
         spec.annotations.get(name, t.Any),
         field(default=defaults[name]) if name in defaults else field())
        for name in spec.args
    ]


def identity(obj):
    """identity function, returns input unmodified"""
    return obj


@dataclass(frozen=True)
class flip:
    """create a function with flipped arguments"""
    func: t.Callable[[t.Any, t.Any], t.Any]

    def __call__(self, a, b):
        return self.func(b, a)


# TODO: __signature__
@dataclass(init=False)
class compose:
    """compose a function from a chain of functions"""
    funcs: t.Tuple[t.Callable, ...]

    def __init__(self, *funcs):
        self.funcs = funcs

    def __call__(self, *args, **kwargs):
        if not self.funcs:
            return identity(*args, **kwargs)
        *tail, head = self.funcs
        value = head(*args, **kwargs)
        for func in reversed(tail):
            value = func(value)
        return value


@dclass
class called_as_method:
    """decorate a callable (e.g. class or function) to be called as a method.
    I.e. the parent instance is passed as the first argument"""
    target: t.Callable

    def __get__(self, instance, cls):
        return (self.target if instance is None
                else partial(self.target, instance))


# TODO: types, docstring
def yieldmap(func, gen) -> t.Generator:
    gen = iter(gen)
    assert inspect.getgeneratorstate(gen) == 'GEN_CREATED'
    item = next(gen)
    while True:
        item = gen.send((yield func(item)))


# TODO: types, docstring
def sendmap(func, gen) -> t.Generator:
    gen = iter(gen)
    assert inspect.getgeneratorstate(gen) == 'GEN_CREATED'
    item = next(gen)
    while True:
        item = gen.send(func((yield item)))


# TODO: types, docstring
def nest(gen, pipe):
    gen = iter(gen)
    assert inspect.getgeneratorstate(gen) == 'GEN_CREATED'
    item = next(gen)
    while True:
        sent = yield from pipe(item)
        try:
            item = gen.send(sent)
        except StopIteration as e:
            return e.value


# TODO: types, docstring
def returnmap(func, gen):
    gen = iter(gen)
    assert inspect.getgeneratorstate(gen) == 'GEN_CREATED'
    return func((yield from gen))


# TODO: types, docstring, signature
@dclass
class oneyield:
    func: t.Callable

    def __call__(self, *args, **kwargs):
        return (yield self.func(*args, **kwargs))


# TODO: types, docstring, signature
@dclass
class onerecieve:
    func: t.Callable

    def __call__(self, obj):
        return self.func((yield obj))


# TODO inner types
def valmap(func: t.Callable, mapping: t.Mapping) -> t.Mapping:
    """map() for values of a mapping"""
    return {k: func(v) for k, v in mapping.items()}


# TODO inner types
def valfilter(predicate: t.Callable, mapping: t.Mapping) -> t.Mapping:
    """filter() for values of a mapping"""
    return {k: v for k, v in mapping.items() if predicate(v)}


def push(value, *funcs):
    """pipe a value through a sequence of functions"""
    for func in funcs:
        value = func(value)
    return value


def as_tuple(dclass):
    """like dataclasses.astuple(), but without recursing into fields"""
    return tuple(getattr(dclass, name) for name in dclass.__dataclass_fields__)


JSONType = t.Union[str, int, float, bool, None,
                   t.Dict[str, t.Any],
                   t.List[t.Any]]
