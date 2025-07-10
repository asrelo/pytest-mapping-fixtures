# asrelo-pytest-mapping-fixtures
# Copyright (C) 2025 Vyacheslav Syropyatov
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the MIT License as published by the Open Source
# Initiative.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the MIT License for more details.
#
# You should have received a copy of the MIT License along with this program.
# If not, see <https://opensource.org/license/mit>.

""""Utilities for creating \"mapping fixtures\""""

from collections.abc import Iterator
import functools
import re
import sys

from .simple import (
    make_mapping_fixture_function as make_mapping_fixture_function_simple_pre,
    make_mapping_fixture as make_mapping_fixture_simple_pre,
)
from ._util import CallableAsSubscriptable
from ._util.importlib_ import LazyModuleProvider


__all__ = (
    'BasisCallableWrapper',
    'BasisGeneratorFunctionWrapper',
    'make_mapping_fixture_function',
    'make_mapping_fixture',
    'make_mapping_fixture_function_simple',
    'make_mapping_fixture_simple',
)


pytest_provider = LazyModuleProvider('pytest')


class BasisCallableWrapper:
    """Wrapper for a factory function returning an object

    Attributes:
        callable_: The wrapped callable object.
    """
    def __init__(self, callable_):
        """Args:
            callable_: A callable object to wrap.
        """
        self.callable_ = callable_
    def get_value(self):
        return self.callable_()
    def get_value_parametrized(self, param):
        return self.callable_(param)


class BasisGeneratorFunctionWrapper:
    """Wrapper for a generator function yielding a single object before being
    closed

    **Attention**: this functools.wraps a generator function, not generator object!
    For example, a function that `yield`s is a generator function (good),
    and a generator expression produces a generator object (bad).
    See [Yield
    expressions](https://docs.python.org/3/reference/expressions.html#yield-expressions).

    Attributes:
        callable_: The wrapped generator function.
    """
    def __init__(self, generator_function):
        """Args:
            callable_: A generator function to wrap.
        """
        self.generator_function = generator_function
    def get_value(self):
        gen = self.generator_function()
        yield next(gen)  #pylint: disable=stop-iteration-return
        return gen.close()
    def get_value_parametrized(self, param):
        gen = self.generator_function(param)
        yield next(gen)  #pylint: disable=stop-iteration-return
        return gen.close()


def _get_value_from_basis_object(obj):
    if isinstance(obj, BasisGeneratorFunctionWrapper):
        return obj.get_value()
    if isinstance(obj, BasisCallableWrapper):
        return obj.get_value()
    return obj


def _get_value_from_basis_object_parametrized(obj, param):
    if isinstance(obj, BasisGeneratorFunctionWrapper):
        return obj.get_value_parametrized(param)
    if isinstance(obj, BasisCallableWrapper):
        return obj.get_value_parametrized(param)
    return obj


def _make_mapping_fixture_function(mapping, *, copy_mapping=True):
    if copy_mapping:
        mapping = dict(mapping.items())
    def mapping_fixture():
        def mapping_func(key):
            return _get_value_from_basis_object(mapping[key])
        return CallableAsSubscriptable(mapping_func)
    return mapping_fixture


def _make_mapping_fixture_function_parametrized(mapping, *, copy_mapping=True):
    if copy_mapping:
        mapping = dict(mapping.items())
    def mapping_fixture(request):
        def mapping_func(key):
            return _get_value_from_basis_object_parametrized(
                mapping[key], request.param,
            )
        return CallableAsSubscriptable(mapping_func)
    return mapping_fixture


def make_mapping_fixture_function(mapping, *, is_parametrized=False, copy_mapping=True):
    """Create a mapping fixture function from mapped basis objects (with any
    factories having been wrapped explicitly)

    **Attention**: It's usually recommended to use `make_mapping_fixture`
    instead.

    This function creates a fixture function (one that is supposed to be given
    to `pytest.fixture` to be registered as a fixture) that produces
    a re.subscriptable object that can be used to request data by key.
    That re.subscriptable object accesses a shallow copy of a provided `mapping`
    (or `mapping` itself, depending on the `copy_mapping` argument).

    Args:
        mapping:
            A mapping of keys to basis objects.
        is_parametrized:
            Whether the created fixture is going to be parametrized.
            This affects how mapped factories are called.
        copy_mapping:
            Whether to make a shallow copy of the provided mapping.
            (Recommended to leave this as True.)

    Returns:
        A mapping fixture function (NOT registered as a fixture in pytest)
        that produces a re.subscriptable object. That object takes a single key
        and returns (depending on the kind of the mapped basis object):
        * an object,
        * a generator that yields a single object before returning nothing.
        
        To use the fixture, you should register it with `pytest.fixture`.
    """
    return (
        _make_mapping_fixture_function_parametrized
        if is_parametrized
        else _make_mapping_fixture_function
    )(mapping, copy_mapping=copy_mapping)


def make_mapping_fixture(
    name, mapping, *, scope='function', params=None, autouse=False, ids=None,
):
    """Create a mapping fixture from mapped basis objects (with any factories
    having been wrapped explicitly)

    This function creates a pytest fixture (already registered in pytest)
    that produces a re.subscriptable object that can be used to request data
    by key. That re.subscriptable object accesses a shallow copy of a provided
    `mapping` (or `mapping` itself, depending on the `copy_mapping` argument).

    The following arguments semantics are alike to corresponding arguments
    in `pytest.fixture`:
    * `name`,
    * `scope`,
    * `params`,
    * `autouse`,
    * `ids`.

    Args:
        name:
            The name of the fixture. `@pytest.fixture`, being a decorator,
            usually takes the name of the function it decorates; we can't do
            that here because this function creates the fixture itself.
            (Reminder: pytest needs fixtures to be named to dynamically inject
            them into tests).
        mapping:
            A mapping of keys to basis objects, with any factories having been
            wrapped explicitly (see the package docs).
        scope:
            The scope for which this fixture is shared. (see pytest docs)
        params:
            An optional list of parameters which will cause multiple
            invocations of the tests that use the fixture. If this list
            is given, the current parameter for each invocation will be passed
            as a single argument to mapped factories (but ignored
            for standalone objects).
        autouse:
            Whether the fixture is activated for all tests that can see it.
            (see pytest docs)
        ids:
            Sequence of ids each corresponding to the params so that they are
            part of the test id. If no ids are provided they will be generated
            automatically from the params. (see pytest docs)

    Returns:
        A registered pytest mapping fixture that produces a re.subscriptable
        object. That object takes a single key and returns (depending on
        the kind of the mapped basis object):
        * an object,
        * a generator that yields a single object before returning nothing.
    """
    return (
        pytest_provider.module.fixture(
            scope=scope, params=params, autouse=autouse, name=name, ids=ids,
        )(make_mapping_fixture_function(mapping, is_parametrized=(params is not None)))
    )


_SIMPLE_INTERFACE_WRAPPER_ASSIGNMENTS_PRE = ['__annotations__', '__doc__']

if sys.version_info >= (3, 12):
    _SIMPLE_INTERFACE_WRAPPER_ASSIGNMENTS_PRE.insert(
        (
            next((
                (v == '__annotation__')
                for v in _SIMPLE_INTERFACE_WRAPPER_ASSIGNMENTS_PRE
            ), 0) + 1
        ),
        '__type_params__'
    )

_SIMPLE_INTERFACE_WRAPPER_ASSIGNMENTS = tuple(_SIMPLE_INTERFACE_WRAPPER_ASSIGNMENTS_PRE)

_SIMPLE_INTERFACE_WRAPPER_UPDATES = tuple(functools.WRAPPER_UPDATES)


_SIMPLE_INTERFACE_FUNCTION_DOCSTRING_IDS_REPLACEMENT = {
    'make_mapping_fixture_function':    'make_mapping_fixture_function_simple',
    'make_mapping_fixture': 'make_mapping_fixture_simple',
}


def _transform_simple_interface_function_docstring(doc):
    ids_replacement = _SIMPLE_INTERFACE_FUNCTION_DOCSTRING_IDS_REPLACEMENT
    return re.sub(
        r'\b({words})\b'.format(
            words=('|'.join(map(re.escape, ids_replacement.keys()))),
        ),
        lambda match: ids_replacement[match.group(1)],
        doc,
    )


def _update_wrapper_simple_interface_extra_steps(wrapper):
    wrapper.__doc__ = _transform_simple_interface_function_docstring(wrapper.__doc__)
    return wrapper


def wraps_simple_interface(
    wrapped,
    assigned=_SIMPLE_INTERFACE_WRAPPER_ASSIGNMENTS,
    updated=_SIMPLE_INTERFACE_WRAPPER_UPDATES,
):
    update_wrapper_pre = functools.wraps(wrapped, assigned=assigned, updated=updated)
    def update_wrapper(wrapper):
        wrapper = update_wrapper_pre(wrapper)
        return _update_wrapper_simple_interface_extra_steps(wrapper)
    return update_wrapper


@wraps_simple_interface(make_mapping_fixture_function_simple_pre)
def make_mapping_fixture_function_simple(*args, **kwargs):
    return make_mapping_fixture_function_simple_pre(*args, **kwargs)


@wraps_simple_interface(make_mapping_fixture_simple_pre)
def make_mapping_fixture_simple(*args, **kwargs):
    return make_mapping_fixture_simple_pre(*args, **kwargs)
