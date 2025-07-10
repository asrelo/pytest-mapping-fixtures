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

import importlib


class LazyModuleProvider:
    def __init__(self, module, package=None):
        self._module_obj = None
        self._module = module
        self._package = package
    @property
    def module(self):
        if self._module_obj is None:
            self._module_obj = importlib.import_module(self._module, self._package)
        return self._module_obj
