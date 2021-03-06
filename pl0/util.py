# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


class ReprMixin:
    """Add a __repr__ that uses __slots__."""

    def __repr__(self):
        assert self.__slots__ is not None, "{} doesn't define __slots__".format(
            self.__class__.__name__)
        assert isinstance(
            self.__slots__,
            tuple), '__slots__ must be a tuple, found a {}'.format(type(
                self.__slots__))
        names = self.__slots__
        values = (getattr(self, x, None) for x in names)
        pairs = ('{}={!r}'.format(x, y) for x, y in zip(names, values))
        joined = ' '.join(pairs)
        return '{}({})'.format(self.__class__.__name__, joined)


def typename(obj):
    return obj.__class__.__name__.lower()


class Node:
    def __init__(self):
        self._children = []

    def __setattr__(self, name, value):
        if name.startswith('_'):
            pass
        elif name in self._children:
            pass
        else:
            self._children.append(name)

        super().__setattr__(name, value)

    def __iter__(self):
        return iter(getattr(self, x) for x in self._children)

    def items(self):
        return [(x, getattr(self, x)) for x in self._children]

    def append(self, *vals):
        for value in vals:
            setattr(self, 'i{}'.format(len(self._children)), value)

    def dump(self, name='', remain=-1, indent=0):
        self._dump(name, self, remain, indent, set())

    def _dump(self, name, item, remain, indent, seen):
        if remain == 0:
            return

        if isinstance(item, (list, tuple)):
            print('// {}{}: ['.format('  ' * indent, name))
            for idx, i in enumerate(item):
                self._dump('[{}]'.format(idx), i, remain, indent + 1, seen)
        elif item in seen:
            return
        else:
            seen.add(item)
            print('// {}{}: {}'.format('  ' * indent, name, item))
            if item is not None and isinstance(item, Node):
                for key, child in item.items():
                    self._dump(key, child, remain - 1, indent + 1, seen)
