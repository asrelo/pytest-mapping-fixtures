# asrelo-pytest-mapping-fixtures

Utilities for creating "mapping fixtures" for **pytest**. That is how we call a fixture that produces a function that receives a key and returns the corresponding value. This was developed as a (somewhat) convenient solution to pytest's inability to process fixtures passed to a test through `pytest.parametrize`.

See detailed docs in `pytest_mapping_fixtures/__init__.py`.

## License

This software is currently distributed under the terms of the MIT License.
