"""Code to work with Global IDs"""

from __future__ import annotations
import re


__all__ = [
    'GlobalId', 'GID'
]


class GlobalId:
    """Represents a Global ID.

    Attributes:
        gid: A 32-bit unsigned integer representation.
        w1: The high word in a 2-part representation.
        w2: The low word in a 2- or 3-part representation.
        b1: The high byte of w1 in a 3-part representation.
        b2: The low byte of w1 in a 3-part representation.

    Notes:
        This class is *not* thread-safe.

        The following attributes are used to implement the above:

            - _gid
    """

    _gid: int

    def __init__(self, **kwargs) -> None:
        """Initializes a GlobalId object.

        You must specify either parts or int (not both, and neither).

        Arguments:
            parts: A tuple of two or three parts (w1, w2) or (b1, b2, w2).
            int: The GlobalID as a 32-bit int.
            bytes: A 4-byte bytes of the GID (big endian)

        Raises:
            ValueError: if any of the values are outside valid ranges.
        """

        kwargs_set = set(kwargs).intersection({'parts', 'int', 'bytes'})

        match len(kwargs_set):
            case 0:
                raise TypeError('__init__ expected 1 argument, got 0')
            case 1:
                pass
            case _:
                raise TypeError(
                    f'__init__ expected 1 argument, got {len(kwargs)}'
                )

        self._gid = 0x00000000

        if 'parts' in kwargs:
            match kwargs['parts']:
                case (w1, w2):
                    self.w1 = w1
                    self.w2 = w2
                case (b1, b2, w2):
                    self.b1 = b1
                    self.b2 = b2
                    self.w2 = w2
                case _:
                    raise ValueError(kwargs['parts'])
        elif 'bytes' in kwargs:
            self._gid = int.from_bytes(
                kwargs['bytes'], byteorder='big', signed=False
            )
        else:
            self._gid = kwargs['int']

    def __int__(self) -> int:
        return self._gid

    def __bytes__(self) -> bytes:
        return self.to_bytes(byteorder='big')

    def to_bytes(self, byteorder: str = 'big') -> bytes:
        """Returns the GlobalId as a Python bytes.

        Arguments:
            byteorder: Either 'big' or 'small'

        Returns:
            The GlobalId in the specified byte order.
        """

        return self._gid.to_bytes(4, byteorder=byteorder, signed=False)

    @property
    def gid(self) -> int:
        return self._gid

    @property
    def w1(self) -> int:
        return self._gid >> 16

    @w1.setter
    def w1(self, value: int) -> None:
        if 0 <= value <= 0xFFFF:
            self._gid = (value << 16) | (self._gid & 0x0000FFFF)
        else:
            raise ValueError(value)

    @property
    def w2(self) -> int:
        return (self._gid & 0x0000FFFF)

    @w2.setter
    def w2(self, value: int) -> None:
        if 0 <= value <= 0xFFFF:
            self._gid = (self._gid & 0xFFFF0000) | value
        else:
            raise ValueError(value)

    @property
    def b1(self) -> int:
        return self._gid >> 24

    @b1.setter
    def b1(self, value: int) -> None:
        if 0 <= value <= 0xFF:
            self._gid = (value << 24) | (self._gid & 0x00FFFFFF)
        else:
            raise ValueError(value)

    @property
    def b2(self) -> int:
        return (self._gid & 0x00FF0000) >> 16

    @b2.setter
    def b2(self, value: int) -> None:
        if 0 <= value <= 0xFF:
            self._gid = (self._gid & 0xFF00FFFF) | (value << 16)
        else:
            raise ValueError(value)

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return self.str2()

    def str2(self) -> str:
        """Returns a GID as a 2-part formatted string."""

        return f'{self.w1}-{self.w2}'

    def str3(self) -> str:
        """Returns a GID as a 3-part formatted string."""

        return f'{self.b1}-{self.b2}-{self.w2}'

    @classmethod
    def from_str(cls, string: str) -> GlobalId:
        """Creates a GlobalId from a text string.

        Arguments:
            string: A Global ID in the xxx-yyy or xxx-yyy-zzz format.

        Returns:
            A newly created GlobalID object.

        Raises:
            ValueError: If the string is not in a valid 2- or 3-part format.
        """

        parts = string.split('-')

        match parts:
            case (w1, w2):
                return cls(parts=(int(w1), int(w2)))
            case (b1, b2, w2):
                return cls(parts=(int(b1), int(b2), int(w2)))
            case _:
                raise ValueError(string)


# For convenience
GID = GlobalId