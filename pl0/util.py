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
