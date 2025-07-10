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

class CallableAsSubscriptable:
    def __init__(self, callable_):
        self._callable = callable_
    @property
    def callable_(self):
        return self._callable
    def __call__(self, arg):
        return self._callable(arg)
    def __getitem__(self, arg):
        return self._callable(arg)
