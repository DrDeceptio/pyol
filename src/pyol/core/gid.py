"""Code to work with Global Identifiers."""


from typing import Literal, Self


__all__ = ['GlobalId', 'GID']


class GlobalId:
    """A global identifier represented by an (unsigned) 32-bit value.

    Attributes:
        gid: The global id as an (unsigned) 32-bit value.
    """

    gid: int

    def __init__(self, gid: int) -> None:
        """Initializes a GlobalId instance.

        Arguments:
            gid: The 32-bit value of the GID.

        Raises:
            ValueError: If gid is an invalid value.
        """

        if not (0 <= gid <= 0xFFFFFFFF):
            raise ValueError(f'Invalid GlobalId value {gid}')
        self.gid = gid

    def __int__(self) -> int:
        return self.gid

    def __bytes__(self) -> bytes:
        return self.to_bytes()

    def __str__(self) -> str:
        if self.b1 != 0:
            return f'{self.b1}-{self.b2}-{self.w2}'
        else:
            return f'{self.w1}-{self.w2}'

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(gid={self.gid})'

    @property
    def b1(self) -> int:
        return (self.gid >> 24) & 0xFF

    @b1.setter
    def b1(self, value: int) -> None:
        if not (0 <= value <= 0xFF):
            raise ValueError(f'Invalid b1 value {value}')

        self.gid = (self.gid & 0x00FFFFFF) | (value << 24)

    @property
    def b2(self) -> int:
        return (self.gid & 0x00FF0000) >> 16

    @b2.setter
    def b2(self, value: int) -> None:
        if not (0 <= value <= 0xFF):
            raise ValueError(f'Invalid b2 value {value}')

        self.gid = (self.gid & 0xFF00FFFF) | (value << 16)

    @property
    def w1(self) -> int:
        return (self.gid & 0xFFFF0000) >> 16

    @w1.setter
    def w1(self, value: int) -> None:
        if not (0 <= value <= 0xFFFF):
            raise ValueError(f'Invalid w1 value {value}')

        self.gid = (self.gid & 0x0000FFFF) | (value << 16)

    @property
    def w2(self) -> int:
        return self.gid & 0x0000FFFF

    @w2.setter
    def w2(self, value: int) -> None:
        if not (0 <= value <= 0xFFFF):
            raise ValueError(f'Invalid w2 value {value}')

        self.gid = (self.gid & 0xFFFF0000) | value

    def to_bytes(self, byteorder: Literal['big', 'little'] = 'big') -> bytes:
        """Converts a GlobalId to Python bytes.

        Arguments:
            byteorder: Either the string 'big' or 'little'

        Returns:
            The GlobalId as 4 Python bytes

        Raises
            ValueError: If byteorder is not 'big' or 'little'.
        """

        if byteorder not in ['big', 'little']:
            raise ValueError(f'Invalid byteorder {byteorder}')

        return self.gid.to_bytes(length=4, byteorder=byteorder)

    @classmethod
    def from_bytes(
            cls,
            data: bytes,
            byteorder: Literal['big', 'little'] = 'big'
    ) -> Self:
        """Creates a new GlobalId from Python bytes.

        Arguments:
            data: The GlobalId as Python bytes.
            byteorder: The byte order, either 'big' or 'little'.

        Returns:
            A new GlobalId instance.

        Raises:
            ValueError: If byteorder is invalid, or if len(data) != 4.
        """

        if len(data) != 4:
            raise ValueError(f'Expected 4 bytes, got {len(data)}')

        return cls(int.from_bytes(data, byteorder=byteorder, signed=False))

    @classmethod
    def from_str(cls, string: str) -> Self:
        """Creates a new GlobalId from a string representation.

        Arguments:
            string: The string representation.

        Returns:
            A new GlobalId instance.

        Raises:
            ValueError: If string is an invalid representation.
        """

        parts = string.split('-')

        match len(parts):
            case 1:
                return cls(int(parts[0]))
            case 2:
                return cls.from_tuple((int(parts[0]), int(parts[1])))
            case 3:
                return cls.from_tuple(
                    (int(parts[0]), int(parts[1]), int(parts[2]))
                )
            case _:
                raise ValueError(f'Invalid string for gid {string}')

    @classmethod
    def from_tuple(cls, value: tuple[int, int] | tuple[int, int, int]) -> Self:
        """Creates a new GlobalID from a 2- or 3-tuple.

        Arguments:
            value: The 2- or 3- tuple.

        Raises:
            ValueError: If len(value) > 3 or < 2, or if any individual member
            is out of range.
        """

        if not (2 <= len(value) <= 3):
            raise ValueError(
                f'Only 2 or 3 element tuples are allowed, got {len(value)}'
            )

        if len(value) == 2:
            if (value[0] > 0xFFFF) or (value[1] > 0xFFFF):
                raise ValueError(f'Invalid values {value}')

            gid = (value[0] << 16) | (value[1])
        else:
            if (value[0] > 0xFF) or (value[1] > 0xFF) or (value[2] > 0xFFFF):
                raise ValueError(f'Invalid values {value}')

            gid = (value[0] << 24) | (value[1] << 16) | value[2]

        return cls(gid)


GID = GlobalId
