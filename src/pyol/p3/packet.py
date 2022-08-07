"""Implementation of P3 Packets."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum
from struct import Struct
from typing import ClassVar


__all__ = [
    'crc16_arc', 'PacketType', 'NakError',
    'Packet', 'ClientPacket', 'ServerPacket', 'V3ClientPacket',
    'V3ServerPacket', 'DataPayload', 'V3InitPayload',
    'V3PacketFactory',
]


_crc16_arc_lookup_table = [
    0x0000, 0xC0C1, 0xC181, 0x0140, 0xC301, 0x03C0, 0x0280, 0xC241, 0xC601,
    0x06C0, 0x0780, 0xC741, 0x0500, 0xC5C1, 0xC481, 0x0440, 0xCC01, 0x0CC0,
    0x0D80, 0xCD41, 0x0F00, 0xCFC1, 0xCE81, 0x0E40, 0x0A00, 0xCAC1, 0xCB81,
    0x0B40, 0xC901, 0x09C0, 0x0880, 0xC841, 0xD801, 0x18C0, 0x1980, 0xD941,
    0x1B00, 0xDBC1, 0xDA81, 0x1A40, 0x1E00, 0xDEC1, 0xDF81, 0x1F40, 0xDD01,
    0x1DC0, 0x1C80, 0xDC41, 0x1400, 0xD4C1, 0xD581, 0x1540, 0xD701, 0x17C0,
    0x1680, 0xD641, 0xD201, 0x12C0, 0x1380, 0xD341, 0x1100, 0xD1C1, 0xD081,
    0x1040, 0xF001, 0x30C0, 0x3180, 0xF141, 0x3300, 0xF3C1, 0xF281, 0x3240,
    0x3600, 0xF6C1, 0xF781, 0x3740, 0xF501, 0x35C0, 0x3480, 0xF441, 0x3C00,
    0xFCC1, 0xFD81, 0x3D40, 0xFF01, 0x3FC0, 0x3E80, 0xFE41, 0xFA01, 0x3AC0,
    0x3B80, 0xFB41, 0x3900, 0xF9C1, 0xF881, 0x3840, 0x2800, 0xE8C1, 0xE981,
    0x2940, 0xEB01, 0x2BC0, 0x2A80, 0xEA41, 0xEE01, 0x2EC0, 0x2F80, 0xEF41,
    0x2D00, 0xEDC1, 0xEC81, 0x2C40, 0xE401, 0x24C0, 0x2580, 0xE541, 0x2700,
    0xE7C1, 0xE681, 0x2640, 0x2200, 0xE2C1, 0xE381, 0x2340, 0xE101, 0x21C0,
    0x2080, 0xE041, 0xA001, 0x60C0, 0x6180, 0xA141, 0x6300, 0xA3C1, 0xA281,
    0x6240, 0x6600, 0xA6C1, 0xA781, 0x6740, 0xA501, 0x65C0, 0x6480, 0xA441,
    0x6C00, 0xACC1, 0xAD81, 0x6D40, 0xAF01, 0x6FC0, 0x6E80, 0xAE41, 0xAA01,
    0x6AC0, 0x6B80, 0xAB41, 0x6900, 0xA9C1, 0xA881, 0x6840, 0x7800, 0xB8C1,
    0xB981, 0x7940, 0xBB01, 0x7BC0, 0x7A80, 0xBA41, 0xBE01, 0x7EC0, 0x7F80,
    0xBF41, 0x7D00, 0xBDC1, 0xBC81, 0x7C40, 0xB401, 0x74C0, 0x7580, 0xB541,
    0x7700, 0xB7C1, 0xB681, 0x7640, 0x7200, 0xB2C1, 0xB381, 0x7340, 0xB101,
    0x71C0, 0x7080, 0xB041, 0x5000, 0x90C1, 0x9181, 0x5140, 0x9301, 0x53C0,
    0x5280, 0x9241, 0x9601, 0x56C0, 0x5780, 0x9741, 0x5500, 0x95C1, 0x9481,
    0x5440, 0x9C01, 0x5CC0, 0x5D80, 0x9D41, 0x5F00, 0x9FC1, 0x9E81, 0x5E40,
    0x5A00, 0x9AC1, 0x9B81, 0x5B40, 0x9901, 0x59C0, 0x5880, 0x9841, 0x8801,
    0x48C0, 0x4980, 0x8941, 0x4B00, 0x8BC1, 0x8A81, 0x4A40, 0x4E00, 0x8EC1,
    0x8F81, 0x4F40, 0x8D01, 0x4DC0, 0x4C80, 0x8C41, 0x4400, 0x84C1, 0x8581,
    0x4540, 0x8701, 0x47C0, 0x4680, 0x8641, 0x8201, 0x42C0, 0x4380, 0x8341,
    0x4100, 0x81C1, 0x8081, 0x4040
]


def crc16_arc(data: bytes) -> int:
    """Computes a CRC16-ARC.

    Arguments:
        data: The data to compute a CRC over.

    Returns:
        The CRC16-ARC value.
    """

    crc = 0
    for byte in data:
        crc = (crc >> 8) ^ _crc16_arc_lookup_table[(crc ^ byte) & 0xFF]

    return crc


class PacketType(IntEnum):
    DATA = 0x20
    SS = 0x21
    SSR = 0x22
    INIT = 0x23
    ACK = 0x24
    NAK = 0x25
    HEARTBEAT = 0x26

    # The following types are undocumented
    RESET = 0x28
    RAK = 0x29
    SETUP = 0x2A
    ACKNOW = 0x2B
    SYNC = 0x5A


class NakError(IntEnum):
    CRC = 0x01
    SEQ = 0x02
    LEN = 0x03


class Payload:
    """Base class for payloads."""

    def __bytes__(self) -> bytes:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    @classmethod
    def from_bytes(cls, payload: bytes) -> Payload:
        """Creates a Payload (subclasS) object from raw bytes.

        Arguments:
            payload: The raw payload bytes.

        Returns:
            A newly-minted Payload (subclass) object.

        Raises:
            ValueError: If payload is too small.
        """

        raise NotImplementedError


# noinspection PyUnresolvedReferences
@dataclass
class Packet:
    """Base class for P3 packets.

    Attributes:
        packet_type: The type of P3 packet.
        tx_seq: The transmit sequence number.
        rx_seq: The receive sequence number.
        payload: The packet's payload.
        sync: The sync byte.
        crc: The CRC16-ARC for the packet (optional in some versions)
        length: The length of the payload + tx_seq + rx_seq + msg_end
        msg_end: The end-of-message marker.
    """

    packet_type: int | PacketType
    tx_seq: int
    rx_seq: int
    payload: bytes | Payload = b''
    sync: int = 0x5A
    crc: int | None = None
    length: int | None = None
    msg_end: bytes = b'\x0D'

    # Used by from_bytes and __bytes__
    _header_struct: ClassVar[Struct] = Struct('!BHHBBB')

    # Used for computing crc in subclasses
    _crc_header_struct: ClassVar[Struct] = Struct('!HBBB')

    def __post_init__(self):
        if self.length is None:
            self.length = len(self.payload) + 3

        if self.crc is None:
            self.crc = self.compute_crc()

    def __str__(self) -> str:
        if isinstance(self.packet_type, PacketType):
            packet_type = self.packet_type.name
        else:
            packet_type = f'0x{self.packet_type:02X}'

        return (
            f'{self.__class__.__name__}('
            f'sync=0x{self.sync:02X}, '
            f'crc=0x{self.crc:04X}, '
            f'length={self.length}, '
            f'tx_seq=0x{self.tx_seq:02X}, '
            f'rx_seq=0x{self.rx_seq:02X}, '
            f'packet_type={packet_type}, '
            f'msg_end=0x{self.msg_end[0]:02X})'
        )

    def __repr__(self) -> str:
        return str(self)

    def is_valid(self, strict: bool = True) -> bool:
        """Checks if a P3 packet is valid.

        Arguments:
            strict: True if only valid values for sync, packet_type, and
                msg_end should be allowed.

        Returns:
            True if the packet is valid, False otherwise.
        """

        is_valid = True

        if strict:
            is_valid = (
                (self.sync == 0x5A)
                and (self.packet_type in PacketType.__members__.values())
                and (self.msg_end == b'\x0D')
            )

        return is_valid and self.is_valid_crc()

    def __bytes__(self) -> bytes:
        raise NotImplementedError

    @classmethod
    def from_bytes(cls, data: bytes) -> Packet:
        """Creates a Packet from raw bytes.

        Arguments:
            data: The raw packet.

        Returns:
            The newly-minted packet object.

        Raises:
            ValueError: If len(data) < 9
        """

        raise NotImplementedError

    def compute_crc(self) -> int:
        """Computes the CRC16-ARC for the packet.

        Returns:
            The computed value.
        """

        raise NotImplementedError

    def is_valid_crc(self) -> bool:
        """Determines if the CRC is valid.

        Returns:
            True if the packet's CRC is valid.
        """

        raise NotImplementedError


class ClientPacket(Packet):
    """For packets sent *from* the client."""

    @classmethod
    def from_bytes(cls, data: bytes) -> ClientPacket:
        if len(data) < 9:
            raise ValueError(f'data too small ({len(data)} bytes)')

        sync, crc, length, tx_seq, rx_seq, packet_type = \
            cls._header_struct.unpack(data[:8])

        msg_end = data[-1:]

        packet_type = packet_type & 0x7F
        if packet_type in PacketType.__members__.values():
            packet_type = PacketType(packet_type)

        payload_len = length - 3
        if payload_len < 0:
            payload_len = 0

        payload = data[8:8+payload_len]     # Payload comes after header

        return cls(
            packet_type=packet_type,
            tx_seq=tx_seq,
            rx_seq=rx_seq,
            payload=payload,
            sync=sync,
            crc=crc,
            msg_end=msg_end
        )

    def __bytes__(self) -> bytes:
        _header_bytes = self._header_struct.pack(
            self.sync,
            self.crc,
            self.length,
            self.tx_seq,
            self.rx_seq,
            self.packet_type | 0x80
        )

        return b''.join([_header_bytes, bytes(self.payload), self.msg_end])

    def compute_crc(self) -> int:
        crc_header_bytes = self._crc_header_struct.pack(
            self.length,
            self.tx_seq,
            self.rx_seq,
            self.packet_type | 0x80
        )

        return crc16_arc(b''.join([crc_header_bytes, bytes(self.payload)]))


class ServerPacket(Packet):
    """For packets sent *from* the server."""

    @classmethod
    def from_bytes(cls, data: bytes) -> ServerPacket:
        if len(data) < 9:
            raise ValueError(f'data too small ({len(data)} bytes)')

        sync, crc, length, tx_seq, rx_seq, packet_type = \
            cls._header_struct.unpack(data[:8])

        msg_end = data[-1:]

        if packet_type in PacketType.__members__.values():
            packet_type = PacketType(packet_type)

        payload_len = length - 3
        if payload_len < 0:
            payload_len = 0

        payload = data[8:8+payload_len]     # Payload comes after header

        return cls(
            packet_type=packet_type,
            tx_seq=tx_seq,
            rx_seq=rx_seq,
            payload=payload,
            sync=sync,
            crc=crc,
            msg_end=msg_end
        )

    def __bytes__(self) -> bytes:
        header_bytes = self._header_struct.pack(
            self.sync,
            self.crc,
            self.length,
            self.tx_seq,
            self.rx_seq,
            self.packet_type
        )

        return b''.join([header_bytes, bytes(self.payload), self.msg_end])

    def compute_crc(self) -> int:
        crc_header_bytes = self._crc_header_struct.pack(
            self.length,
            self.tx_seq,
            self.rx_seq,
            self.packet_type
        )

        return crc16_arc(b''.join([crc_header_bytes, bytes(self.payload)]))


class V3ClientPacket(ClientPacket):
    def is_valid_crc(self) -> bool:
        return self.crc == self.compute_crc()


class V3ServerPacket(ServerPacket):
    def is_valid_crc(self) -> bool:
        return self.crc == self.compute_crc()


# noinspection PyUnresolvedReferences
@dataclass
class DataPayload(Payload):
    """Payload for a DATA (packet_type == 0x20) packet.

    Attributes:
        token: The two-byte token field.
        data: The data for the payload.
    """

    token: bytes
    data: bytes

    def __str__(self) -> str:
        return f'{self.__class__.__name__}(token={self.token})'

    def __bytes__(self) -> bytes:
        return b''.join([self.token, self.data])

    def __len__(self) -> int:
        return len(self.token) + len(self.data)

    @classmethod
    def from_bytes(cls, payload: bytes) -> DataPayload:
        if len(payload) < 2:
            raise ValueError(f'Payload too small ({len(payload)} bytes')

        return cls(token=payload[:2], data=payload[2:])


# noinspection PyUnresolvedReferences
@dataclass
class V3InitPayload(Payload):
    """Init payload for V3 (older) clients.

    Attributes:
        platform: Client platform
        major_ver: Client version major
        minor_ver: Client version minor
        unused: Unused
        machine_memory: Memory on the host.
        app_memory: Memory for the app.
        pc_type: Type of machine (???)
        release_month: Build month of client (???)
        release_day: Build day of client (???)
        customer_class: (???)
        udo_timestamp: UDO timestamp
        dos_ver: DOS version
        session_flags: (???)
        video_type: (???)
        cpu_type: (???)
        media_type: (???)
        win_ver: Version of Windows.
        win_memory_mode: (???)
        horizontal_res: Horizontal resolution.
        vertical_res: Vertical resolution.
        num_colors: Total number of colors supported.
        filler: Filler byte.
        region: (???)
        languages (???)
        connect_speed: (???)
    """

    platform: int = 0x03
    major_ver: int = 0x6E
    minor_ver: int = 0x5F
    unused: int = 0x00
    machine_memory: int = 0x10
    app_memory: int = 0x00
    pc_type: int = 0x0000
    release_month: int = 0x05
    release_day: int = 0x0F
    customer_class: int = 0x00
    udo_timestamp: int = 0x00000000
    dos_ver: int = 0x0000
    session_flags: int = 0x0000
    video_type: int = 0x00
    cpu_type: int = 0x00
    media_type: int = 0x00000000
    win_ver: int = 0x00000000
    win_memory_mode: int = 0x00
    horizontal_res: int = 0x0000
    vertical_res: int = 0x0000
    num_colors: int = 0x0000
    filler: int = 0x00
    region: int = 0x0000
    languages: list[int] = field(default_factory=lambda: [0] * 4)
    connect_speed: int = 0x00

    # Used by from_bytes and __bytes__
    _init_struct: ClassVar[Struct] = Struct(
        '!'  # Network byte order
        'B'  # platform
        'B'  # major_ver
        'B'  # minor_ver
        'B'  # unused
        'B'  # machine_memory
        'B'  # app_memory
        'H'  # pc_type
        'B'  # release_month
        'B'  # release_day
        'H'  # customer_class
        'I'  # udo_timestamp
        'H'  # dos_ver
        'H'  # session_flags
        'B'  # video_type
        'B'  # cpu_type
        'I'  # media_type
        'I'  # win_ver
        'B'  # win_memory_mode
        'H'  # horizontal_res
        'H'  # vertical_res
        'H'  # num_colors
        'B'  # filler
        'H'  # region
        '4H'  # languages
        'B'  # connect_speed
    )

    def __str__(self) -> str:
        return (
            f'{self.__class__.__name__}('
            f'platform={self.platform}, '
            f'major_ver={self.major_ver}, '
            f'minor_ver={self.minor_ver}, '
            f'unused={self.unused}, '
            f'machine_memory={self.machine_memory}, '
            f'app_memory={self.app_memory}, '
            f'pc_type={self.pc_type}, '
            f'release_month={self.release_month}, '
            f'release_day={self.release_day}, '
            f'customer_class={self.customer_class}, '
            f'udo_timestamp=0x{self.udo_timestamp:08X}, '
            f'dos_ver={self.dos_ver}, '
            f'session_flags=0x{self.session_flags:04X}, '
            f'video_type={self.video_type}, '
            f'cpu_type={self.cpu_type}, '
            f'media_type={self.media_type}, '
            f'win_ver=0x{self.win_ver:08X}, '
            f'win_memory_mode={self.win_memory_mode}, '
            f'horizontal_res={self.horizontal_res}, '
            f'vertical_res={self.vertical_res}, '
            f'num_colors={self.num_colors}, '
            f'filler=0x{self.filler:02X}, '
            f'region={self.region}, '
            f'language={self.languages}, '
            f'connect_speed={self.connect_speed})'
        )

    def __repr__(self) -> str:
        return str(self)

    def __len__(self) -> int:
        return self._init_struct.size

    def __bytes__(self) -> bytes:
        return self._init_struct.pack(
            self.platform,
            self.major_ver, self.minor_ver,
            self.unused,
            self.machine_memory, self.app_memory, self.pc_type,
            self.release_month, self.release_day,
            self.customer_class, self.udo_timestamp, self.dos_ver,
            self.session_flags,
            self.video_type, self.cpu_type, self.media_type,
            self.win_ver, self.win_memory_mode,
            self.horizontal_res, self.vertical_res,
            self.num_colors, self.filler,
            self.region,
            self.languages[0],
            self.languages[1],
            self.languages[2],
            self.languages[3],
            self.connect_speed
        )

    @classmethod
    def from_bytes(cls, payload: bytes) -> V3InitPayload:
        if len(payload) < cls._init_struct.size:
            raise ValueError(f'Payload too small: {len(payload)} bytes')

        fields = cls._init_struct.unpack(payload[:49])
        kwargs = {
            'platform': fields[0],
            'major_ver': fields[1],
            'minor_ver': fields[2],
            'unused': fields[3],
            'machine_memory': fields[4],
            'app_memory': fields[5],
            'pc_type': fields[6],
            'release_month': fields[7],
            'release_day': fields[8],
            'customer_class': fields[9],
            'udo_timestamp': fields[10],
            'dos_ver': fields[11],
            'session_flags': fields[12],
            'video_type': fields[13],
            'cpu_type': fields[14],
            'media_type': fields[15],
            'win_ver': fields[16],
            'win_memory_mode': fields[17],
            'horizontal_res': fields[18],
            'vertical_res': fields[19],
            'num_colors': fields[20],
            'filler': fields[21],
            'region': fields[22],
            'languages': list(fields[23:27]),
            'connect_speed': fields[27]
        }

        return cls(**kwargs)


# noinspection PyUnresolvedReferences
class PacketKit:
    """Base class for Packet factories.

    Attributes:
        client_packet_class: The class to create client packets.
        server_packet_class: The class to create server packets.

    Notes:
        Don't use this class directly. Instead, use one of the concrete
        PacketFactory subclasses.
    """

    client_packet_class: ClientPacket = ClientPacket
    server_packet_class: ServerPacket = ServerPacket

    @classmethod
    def client_packet(
            cls,
            packet_type: PacketType,
            tx_seq: int,
            rx_seq: int,
            payload: bytes | Payload = b''
    ) -> ClientPacket:
        """Builds a ClientPacket object.

        Arguments:
            packet_type: The type of P3 packet.
            tx_seq: The transmit sequence number.
            rx_seq: The receive sequence number.
            payload: The packet payload.

        Returns:
            A newly-minted ClientPacket object.
        """

        return cls.client_packet_class(
            packet_type=packet_type,
            tx_seq=tx_seq,
            rx_seq=rx_seq,
            payload=payload
        )

    @classmethod
    def server_packet(
            cls,
            packet_type: PacketType,
            tx_seq: int,
            rx_seq: int,
            payload: bytes | Payload = b''
    ) -> ServerPacket:
        """Builds a ServerPacket object.

        Arguments:
            packet_type: The type of P3 packet.
            tx_seq: The transmit sequence number.
            rx_seq: The receive sequence number.
            payload: The packet payload.

        Returns:
            A newly-minted ServerPacket object.
        """

        return cls.server_packet_class(
            packet_type=packet_type,
            tx_seq=tx_seq,
            rx_seq=rx_seq,
            payload=payload
        )

    @classmethod
    def client_packet_from_bytes(cls, data: bytes) -> ClientPacket:
        """Builds a ClientPacket object from raw bytes.

        Arguments:
            data: The raw packet data.

        Returns:
            A newly-minted ClientPacket object.
        """

        return cls.client_packet_class.from_bytes(data)

    @classmethod
    def server_packet_from_bytes(cls, data: bytes) -> ServerPacket:
        """Builds a ServerPacket object from raw bytes.

        Arguments:
            data: The raw packet data.

        Returns:
            A newly-minted ServerPacket object.
        """

        return cls.server_packet_class.from_bytes(data)

    @classmethod
    def client_data_packet(
            cls,
            tx_seq: int,
            rx_seq: int,
            token: bytes,
            data: bytes
    ) -> ClientPacket:
        """Builds a DATA packet for sending from a client.

        Arguments:
            tx_seq: The transmit sequence number.
            rx_seq: The receive sequence number.
            token: The two-byte token field.
            data: The data for the payload.

        Returns:
            A newly-minted ClientPacket object.
        """

        return cls.client_packet(
            packet_type=PacketType.DATA,
            tx_seq=tx_seq,
            rx_seq=rx_seq,
            payload=DataPayload(token=token, data=data)
        )

    @classmethod
    def server_data_packet(
            cls,
            tx_seq: int,
            rx_seq: int,
            token: bytes,
            data: bytes
    ) -> ServerPacket:
        """Builds a DATA packet for sending from a server.

        Arguments:
            tx_seq: The transmit sequence number.
            rx_seq: The receive sequence number.
            token: The two-byte token field.
            data: The data for the payload.

        Returns:
            A newly-minted ServerPacket object.
        """

        return cls.server_packet(
            packet_type=PacketType.DATA,
            tx_seq=tx_seq,
            rx_seq=rx_seq,
            payload=DataPayload(token=token, data=data)
        )

    @classmethod
    def client_ack_packet(cls, tx_seq: int, rx_seq: int) -> ClientPacket:
        """Builds an ACK packet for sending from a client.

        Arguments:
            tx_seq: The transmit sequence number.
            rx_seq: The receive sequence number.

        Returns:
            A newly-minted ClientPacket object.
        """

        return cls.client_packet(
            packet_type=PacketType.ACK,
            tx_seq=tx_seq,
            rx_seq=rx_seq
        )

    @classmethod
    def server_ack_packet(cls, tx_seq: int, rx_seq: int) -> ServerPacket:
        """Builds an ACK packet for sending from a server.

        Arguments:
            tx_seq: The transmit sequence number.
            rx_seq: The receive sequence number.

        Returns:
            A newly-minted ServerPacket object.
        """

        return cls.server_packet(
            packet_type=PacketType.ACK,
            tx_seq=tx_seq,
            rx_seq=rx_seq
        )

    @classmethod
    def client_nak_packet(
            cls,
            tx_seq: int,
            rx_seq: int,
            nak_err: int | NakError
    ) -> ClientPacket:
        """Builds a NAK packet for sending from a client.

        Arguments:
            tx_seq: The transmit sequence number.
            rx_seq: The receive sequence number.
            nak_err: The NAK error message byte.

        Returns:
            A newly-minted ClientPacket object.
        """

        payload = nak_err.to_bytes(length=1, byteorder='big')
        return cls.client_packet(
            packet_type=PacketType.NAK,
            tx_seq=tx_seq,
            rx_seq=rx_seq,
            payload=payload
        )

    @classmethod
    def server_nak_packet(
            cls,
            tx_seq: int,
            rx_seq: int,
            nak_err: int | NakError
    ) -> ServerPacket:
        """Builds a NAK packet for sending from a server.

        Arguments:
            tx_seq: The transmit sequence number.
            rx_seq: The receive sequence number.
            nak_err: The NAK error message byte.

        Returns:
            A newly-minted ServerPacket object.
        """

        payload = nak_err.to_bytes(length=1, byteorder='big')
        return cls.server_packet(
            packet_type=PacketType.NAK,
            tx_seq=tx_seq,
            rx_seq=rx_seq,
            payload=payload
        )

    @classmethod
    def client_heartbeat_packet(cls, tx_seq: int, rx_seq: int) -> ClientPacket:
        """Builds a heartbeat packet for sending from a client.

        Arguments:
            tx_seq: The transmit sequence number.
            rx_seq: The receive sequence number.

        Returns:
            A newly-minted ClientPacket object.
        """

        return cls.client_packet(
            packet_type=PacketType.HEARTBEAT,
            tx_seq=tx_seq,
            rx_seq=rx_seq
        )

    @classmethod
    def server_heartbeat_packet(cls, tx_seq: int, rx_seq: int) -> ServerPacket:
        """Builds a heartbeat packet for sending from a server.

        Arguments:
            tx_seq: The transmit sequence number.
            rx_seq: The receive sequence number.

        Returns:
            A newly-minted ClientPacket object.
        """

        return cls.server_packet(
            packet_type=PacketType.HEARTBEAT,
            tx_seq=tx_seq,
            rx_seq=rx_seq
        )

    @classmethod
    def data_payload(cls, token: bytes, data: bytes) -> DataPayload:
        """Builds a new DataPayload object.

        Arguments:
            token: The two-byte token field.
            data: The payload data.

        Returns:
            A newly-minted DataPayload object.
        """

        return DataPayload(token=token, data=data)

    @classmethod
    def data_payload_from_bytes(cls, payload: bytes) -> DataPayload:
        """Builds a DataPayload object from raw bytes.

        Arguments:
            payload: The raw payload bytes.

        Returns:
            A newly-minted DataPayload object.
        """

        return DataPayload.from_bytes(payload)

    @classmethod
    def init_payload(cls, **kwargs) -> Payload:
        """Builds an InitPayload object.

        Returns:
            A newly-minted InitPayload object.
        """

        raise NotImplementedError

    @classmethod
    def init_payload_from_bytes(cls, payload: bytes) -> Payload:
        """Builds an InitPayload object from raw bytes.

        Arguments:
            payload: The raw init payload bytes.

        Returns:
            A newly-minted InitPayload object.
        """

        raise NotImplementedError


class V3PacketFactory(PacketKit):
    client_packet_class = V3ClientPacket
    server_packet_class = V3ServerPacket

    @classmethod
    def init_payload(
            cls,
            platform: int = 0x03,
            major_ver: int = 0x6E,
            minor_ver: int = 0x5F,
            unused: int = 0x00,
            machine_memory: int = 0x10,
            app_memory: int = 0x00,
            pc_type: int = 0x0000,
            release_month: int = 0x05,
            release_day: int = 0x0F,
            customer_class: int = 0x00,
            udo_timestamp: int = 0x00000000,
            dos_ver: int = 0x0000,
            session_flags: int = 0x0000,
            video_type: int = 0x00,
            cpu_type: int = 0x00,
            media_type: int = 0x00000000,
            win_ver: int = 0x00000000,
            win_memory_mode: int = 0x00,
            horizontal_res: int = 0x0000,
            vertical_res: int = 0x0000,
            num_colors: int = 0x0000,
            filler: int = 0x00,
            region: int = 0x0000,
            languages: list[int] | None = None,
            connect_speed: int = 0x00,
    ) -> V3InitPayload:

        if languages is None:
            languages = [0] * 4

        return V3InitPayload(
            platform=platform,
            major_ver=major_ver,
            minor_ver=minor_ver,
            unused=unused,
            machine_memory=machine_memory,
            app_memory=app_memory,
            pc_type=pc_type,
            release_month=release_month,
            release_day=release_day,
            customer_class=customer_class,
            udo_timestamp=udo_timestamp,
            dos_ver=dos_ver,
            session_flags=session_flags,
            video_type=video_type,
            cpu_type=cpu_type,
            media_type=media_type,
            win_ver=win_ver,
            win_memory_mode=win_memory_mode,
            horizontal_res=horizontal_res,
            vertical_res=vertical_res,
            num_colors=num_colors,
            filler=filler,
            region=region,
            languages=languages,
            connect_speed=connect_speed
        )

    @classmethod
    def init_payload_from_bytes(cls, payload: bytes) -> V3InitPayload:
        return V3InitPayload.from_bytes(payload)
