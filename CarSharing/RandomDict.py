# coding=utf-8
"""
    Python dictionaries with O(1) random element access.

    Adapted from https://github.com/NicoDeGiacomo/randomdict/blob/master/randomdict.py

    Added by Dries: + Ability to use preset rng for deterministic random.
                    + Made this class more like a real dict, with __contains__, keys, values, items, ...
"""
from collections import MutableMapping
import random
import typing

__version__ = '0.2.0'


class RandomDict(MutableMapping):
    """
    Python dictionaries with O(1) random element access.
    """

    def __init__(self, *args, **kwargs):
        """ Create RandomDict object with contents specified by arguments.
        Any argument
        :param *args:       dictionaries whose contents get added to this dict
        :param **kwargs:    key, value pairs will be added to this dict
        """
        # mapping of keys to array positions
        self._keys = {}
        self._values = []
        self._last_index = -1
        self._rng = random

        self.update(*args, **kwargs)

    def __setitem__(self, key, val):
        if key in self._keys:
            i = self._keys[key]
            self._values[i] = (key, val)
        else:
            self._last_index += 1
            i = self._last_index
            self._values.append((key, val))
        self._keys[key] = i

    def __delitem__(self, key):
        if key not in self._keys:
            raise KeyError

        # index of item to delete is i
        i = self._keys[key]
        # last item in values array is
        move_key, move_val = self._values.pop()

        if i != self._last_index:
            # we move the last item into its location
            self._values[i] = (move_key, move_val)
            self._keys[move_key] = i
        # else it was the last item and we just throw
        # it away

        # shorten array of values
        self._last_index -= 1
        # remove deleted key
        del self._keys[key]

    def __getitem__(self, key):
        if key not in self._keys:
            raise KeyError

        i = self._keys[key]
        return self._values[i][1]

    def __iter__(self):
        return iter(self._keys)

    def __len__(self):
        return self._last_index + 1

    def __contains__(self, key):
        return key in self._keys

    def items(self):
        return self._values

    def keys(self):
        return self._keys.keys()

    def values(self):
        return map(lambda x: x[1], self._values)

    def random_key(self):
        """ Return a random key from this dictionary in O(1) time """
        if len(self) == 0:
            raise KeyError("RandomDict is empty")

        i = self._rng.randint(0, self._last_index)
        return self._values[i][0]

    def random_value(self):
        """ Return a random value from this dictionary in O(1) time """
        return self[self.random_key()]

    def random_item(self):
        """ Return a random key-value pair from this dictionary in O(1) time """
        k = self.random_key()
        return k, self[k]

    def copy(self):
        return RandomDict.from_random(self._rng, self.items())

    @classmethod
    def from_random(cls, rng, *args, **kwargs):
        instance = cls(*args, **kwargs)
        instance.rng = rng
        return instance


class RandomDictType(RandomDict, typing.MutableMapping[typing.KT, typing.VT], extra=RandomDict):
    __slots__ = ()
