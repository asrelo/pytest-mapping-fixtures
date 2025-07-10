# asrelo-pytest-mapping-fixtures
# Copyright (C) 2025 Vyacheslav Syropiatov
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

"""The implementation of the "simple" interface in relation to basis objects
(see the package docs)."""

from collections.abc import Iterator

from ._util import CallableAsSubscriptable
from ._util.importlib_ import LazyModuleProvider


__all__ = (
    'make_mapping_fixture_function',
    'make_mapping_fixture',
)


pytest_provider = LazyModuleProvider('pytest')


def _get_value_from_basis_object(obj):
    if callable(obj):
        res = obj()
        if isinstance(res, Iterator):
            yield next(res)  #pylint: disable=stop-iteration-return
            return res.close()
        return res
    return obj


def _get_value_from_basis_object_parametrized(obj, param):
    if callable(obj):
        res = obj(param)
        if isinstance(res, Iterator):
            yield next(res)  #pylint: disable=stop-iteration-return
            return res.close()
        return res
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


def make_mapping_fixture_function(
    mapping, *, is_parametrized=False, copy_mapping=True,
):
    """Create a mapping fixture function from mapped basis objects (trying
    to detect factories automatically)

    **Attention**: It's usually recommended to use `make_mapping_fixture`
    instead.

    This function creates a fixture function (one that is supposed to be given
    to `pytest.fixture` to be registered as a fixture) that produces
    a subscriptable object that can be used to request data by key.
    That subscriptable object accesses a shallow copy of a provided `mapping`
    (or `mapping` itself, depending on the `copy_mapping` argument).

    **Attention**: This function has a "simple" interface in relation to basis
    objects, meaning it tries to detect factories in the mapping on the fly.
    It can make mistakes in certain situations; see the package docs.

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
        that produces a subscriptable object. That object takes a single key
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
    """Create a mapping fixture from mapped basis objects (trying to detect
    factories automatically)

    This function creates a pytest fixture (already registered in pytest)
    that produces a subscriptable object that can be used to request data
    by key. That subscriptable object accesses a shallow copy of a provided
    `mapping` (or `mapping` itself, depending on the `copy_mapping` argument).

    **Attention**: This function has a "simple" interface in relation to basis
    objects, meaning it tries to detect factories in the mapping on the fly.
    It can make mistakes in certain situations; see the module docs.

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
            A mapping of keys to basis objects.
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
        A registered pytest mapping fixture that produces a subscriptable
        object. That object takes a single key and returns (depending on
        the kind of the mapped basis object):
        * an object,
        * a generator that yields a single object before returning nothing.
    """
    return (
        pytest_provider.module.fixture(
            scope=scope, params=params, autouse=autouse, name=name, ids=ids,
        )(
            make_mapping_fixture_function(
                mapping, is_parametrized=(params is not None),
            )
        )
    )
