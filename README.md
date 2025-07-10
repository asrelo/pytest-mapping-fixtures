# asrelo-pytest-mapping-fixtures

Utilities for creating "mapping fixtures" for **pytest**. That is how we call a fixture that produces a function that receives a key and returns the corresponding value. This was developed as a (somewhat) convenient solution to pytest's inability to process fixtures passed to a test through `pytest.parametrize`.

A mapping fixture is created from a mapping of some keys to some *basis objects*. Those can be standalone objects or factories for objects. Standalone objects are then provided to code in tests directly (and they are better be immutable). Factories for objects follow the pytest's convention for fixture functions: one either returns the object to be used or yields a single object to be used (pytest's [teardown mechanism](https://docs.pytest.org/en/stable/how-to/fixtures.html#yield-fixtures-recommended)). Factories are either called with no arguments or a single positional argument for a parameter value when the created fixture is parametrized (see below).

Note, you still **cannot just map fixtures** &mdash; that appears to be impossible with pytest, it won't realize that a test depends on those mapped fixtures.

There are 2 ways to give the mapping of basis objects.

* All factories are marked explicitly by wrapping them with a corresponding class:
  * for a factory returning a single object: `BasisCallableWrapper`,
  * for a factory yielding a single object (pytest's teardown mechanism): `BasisGeneratorFunctionWrapper`,
  * standalone objects are not wrapped.

     ```python 
     def factory_1():
         return [-1, 0, 1]

     def factory_2():
         user = create_user()
         yield user
         delete_user(user)

     MAPPING = {
         'a': (1, 2, 3),
         'b': 'abracadabra',
         'c': BasisCallableWrapper(factory_1),
         'd': BasisGeneratorFunctionWrapper(factory_2),
     }
     ```

* Factories are detected on the fly (the "simple" interface). This method can be less verbose and thus more convenient, but it can misidentify factories in certain situations.

  Functions of the "simple" interface are similar to functions of the normal interface and they are marked as `simple` in their names.

  For the "simple" interface, a the algorithm to determine the kind of a basis object is:

  1. If the object is NOT callable, use it directly.
  2. Otherwise, call it and store the resulting object.
  3. If the result is NOT an instance of `Iterator`, conclude that the basis object was a returning factory, and use the resulting object.
  4. Otherwise, conclude that the basis object was the yielding factory, and proceed to request a single object from that iterator to use.

     ```python 
     def factory_1():
         return [-1, 0, 1]

     def factory_2():
         obj = create_env_object()
         yield obj
         delete_env_object(obj)

     MAPPING_SIMPLE = {
         'a': (1, 2, 3),
         'b': 'abracadabra',
         'c': factory_1,
         'd': factory_2,
     }
     ```

The main functions you will probably use most often is `make_mapping_fixture` (or `make_mapping_fixture_simple`). It creates a mapping fixture from mapped basis objects (with any factories having been wrapped explicitly). That fixture is registered in pytest with a given name, so that pytest tests can request them.

```python
contexts_mapping = make_mapping_fixture('contexts_mapping', MAPPING)

@pytest.parametrize('key', tuple(MAPPING.keys()))
def test_parametrized(contexts_mapping, key):
    value = contexts_mapping[key]
    ...
```

The functions that just make the underlying fixture functions are also available: `make_mapping_fixture_function` (or `make_mapping_fixture_function_simple`). You can register them later with `pytest.fixture` (don't forget to pass the `name`).

```python
contexts_mapping = pytest.fixture(
    make_mapping_fixture_function(MAPPING), name='contexts_mapping',
)
```

Mapping fixtures can be created as **methods of classes**, but you **need to wrap** the created object (whether a fixture or a fixture function) with `staticmethod`.

```python
class TestClass:
    contexts_mapping = staticmethod(make_mapping_fixture('contexts_mapping', MAPPING))
```

There is no way to avoid some boilerplate to use some function as a standalone fixture and in a mapping fixture at the same time. The example below shows minimal code for the case of a fixtre that does not depend on any other fixture.

```python
# factory function
def build_context():
    return Context(...)

# creates a fixture named "context"
context = pytest.fixture(name='context')(fixture_context)

# uses the fixture normally
def test_1(context):
    ...

# uses the underlying factory function to create a mapped fixture
contexts_mapping = make_mapping_fixture_simple('context_mapped', {0: fixture_context})
```

`make_mapping_fixture` (or `make_mapping_fixture_function`) supports arguments for `pytest.fixture`: `scope`, `autouse`. It also supports parametrization, see below.

## Parametrized fixtures

You can also parametrize a mapping fixture. If you do, the parameter value will be given to your factories for each invocation of a test (but discarded for standalone objects).

To parametrize the fixture built by `make_mapping_fixture` (or `make_mapping_fixture_simple`), pass the arguments `params` and optionally `ids` like with `pytest.fixture`.

To make a fixture function for a parametrized fixture with `make_mapping_fixture_function` (or `make_mapping_fixture_function_simple`), pass `is_parametrized=True`. You will need to pass the parameters later to `pytest.fixture`.
