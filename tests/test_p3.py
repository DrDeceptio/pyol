import unittest

from pyol.p3 import (
    PacketType, NakError, crc16_arc, DataPayload, V3InitPayload, V3ClientPacket,
    V3ServerPacket, V3PacketFactory, ClientPacket, ServerPacket
)


class Crc16ArcTestCase(unittest.TestCase):
    def test_crc16_arc(self):
        result = crc16_arc(b'Deceptio')
        self.assertEqual(result, 0xF841)


class DataPayloadTestCase(unittest.TestCase):
    def test__init__(self):
        dp = DataPayload(token=b'AT', data=b'\xDE\xAD\xC0\xDE')
        self.assertEqual(dp.token, b'AT')
        self.assertEqual(dp.data, b'\xDE\xAD\xC0\xDE')

    def test__bytes__(self):
        dp = DataPayload(token=b'AT', data=b'\xDE\xAD\xC0\xDE')
        self.assertEqual(bytes(dp), b'AT\xDE\xAD\xC0\xDE')

    def test__len__(self):
        dp = DataPayload(token=b'AT', data=b'\xDE\xAD\xC0\xDE')
        self.assertEqual(len(dp), 6)

    def test_from_bytes(self):
        dp = DataPayload.from_bytes(b'AT\xDE\xAD\xC0\xDE')
        self.assertEqual(dp.token, b'AT')
        self.assertEqual(dp.data, b'\xDE\xAD\xC0\xDE')

        dp = DataPayload.from_bytes(b'AT')
        self.assertEqual(dp.token, b'AT')
        self.assertEqual(dp.data, b'')

        with self.assertRaises(ValueError):
            DataPayload.from_bytes(b'')

        with self.assertRaises(ValueError):
            DataPayload.from_bytes(b'A')


# noinspection DuplicatedCode
class V3InitPayloadTestCase(unittest.TestCase):
    def test__init__(self):
        payload = V3InitPayload()
        self.assertEqual(payload.platform, 0x03)
        self.assertEqual(payload.major_ver, 0x6E)
        self.assertEqual(payload.minor_ver, 0x5F)
        self.assertEqual(payload.unused, 0x00)
        self.assertEqual(payload.machine_memory, 0x10)
        self.assertEqual(payload.app_memory, 0x00)
        self.assertEqual(payload.pc_type, 0x0000)
        self.assertEqual(payload.release_month, 0x05)
        self.assertEqual(payload.release_day, 0x0F)
        self.assertEqual(payload.customer_class, 0x00)
        self.assertEqual(payload.udo_timestamp, 0x00000000)
        self.assertEqual(payload.dos_ver, 0x0000)
        self.assertEqual(payload.session_flags, 0x0000)
        self.assertEqual(payload.video_type, 0x00)
        self.assertEqual(payload.cpu_type, 0x00)
        self.assertEqual(payload.media_type, 0x00000000)
        self.assertEqual(payload.win_ver, 0x00000000)
        self.assertEqual(payload.win_memory_mode, 0x00)
        self.assertEqual(payload.horizontal_res, 0x0000)
        self.assertEqual(payload.vertical_res, 0x0000)
        self.assertEqual(payload.num_colors, 0x0000)
        self.assertEqual(payload.filler, 0x00)
        self.assertEqual(payload.region, 0x0000)
        self.assertEqual(payload.languages, [0x0000] * 4)
        self.assertEqual(payload.connect_speed, 0x00)

    def test_from_bytes(self):
        raw = b''.join([
            b'\x03'                 # payload.platform
            b'\x6E'                 # payload.major_ver
            b'\x5F'                 # payload.minor_ver
            b'\x00'                 # payload.unused
            b'\x10'                 # payload.machine_memory
            b'\x00'                 # payload.app_memory
            b'\x00\x00'             # payload.pc_type
            b'\x05'                 # payload.release_month
            b'\x0F'                 # payload.release_day
            b'\x00\x00'             # payload.customer_class
            b'\x1C\x98\x0B\x3A'     # payload.udo_timestamp
            b'\xC3\xB6'             # payload.dos_ver
            b'\x10\xC0'             # payload.session_flags
            b'\x03'                 # payload.video_type
            b'\x03'                 # payload.cpu_type
            b'\x00\x00\x00\x00'     # payload.media_type
            b'\x04\x00\x00\x00'     # payload.win_ver
            b'\x01'                 # payload.win_memory_mode
            b'\xC0\x06'             # payload.horizontal_res
            b'\x5D\x04'             # payload.vertical_res
            b'\xFF\xFF'             # payload.num_colors
            b'\x00'                 # payload.filler
            b'\x00\x00'             # payload.region
            b'\x00\x00'             # payload.languages[0]
            b'\x00\x00'             # payload.languages[1]
            b'\x00\x00'             # payload.languages[2]
            b'\x00\x00'             # payload.languages[3]
            b'\x02'                 # payload.connect_speed
        ])
        v3ip = V3InitPayload.from_bytes(raw)

        self.assertEqual(v3ip.platform, 0x03)
        self.assertEqual(v3ip.major_ver, 0x6E)
        self.assertEqual(v3ip.minor_ver, 0x5F)
        self.assertEqual(v3ip.unused, 0x00)
        self.assertEqual(v3ip.machine_memory, 0x10)
        self.assertEqual(v3ip.app_memory, 0x00)
        self.assertEqual(v3ip.pc_type, 0x00)
        self.assertEqual(v3ip.release_month, 0x05)
        self.assertEqual(v3ip.release_day, 0x0F)
        self.assertEqual(v3ip.customer_class, 0x0000)
        self.assertEqual(v3ip.udo_timestamp, 0x1C980B3A)
        self.assertEqual(v3ip.dos_ver, 0xC3B6)
        self.assertEqual(v3ip.session_flags, 0x10C0)
        self.assertEqual(v3ip.video_type, 0x03)
        self.assertEqual(v3ip.cpu_type, 0x03)
        self.assertEqual(v3ip.media_type, 0x00000000)
        self.assertEqual(v3ip.win_ver, 0x04000000)
        self.assertEqual(v3ip.win_memory_mode, 0x01)
        self.assertEqual(v3ip.horizontal_res, 0xC006)
        self.assertEqual(v3ip.vertical_res, 0x5D04)
        self.assertEqual(v3ip.num_colors, 0xFFFF)
        self.assertEqual(v3ip.filler, 0x00)
        self.assertEqual(v3ip.region, 0x0000)
        self.assertEqual(v3ip.languages, [0x0000] * 4)
        self.assertEqual(v3ip.connect_speed, 0x02)

    def test__len__(self):
        payload = V3InitPayload()
        self.assertEqual(len(payload), 49)

    def test__bytes__(self):
        payload = V3InitPayload()
        raw = b''.join([
            b'\x03'                 # payload.platform
            b'\x6E'                 # payload.major_ver
            b'\x5F'                 # payload.minor_ver
            b'\x00'                 # payload.unused
            b'\x10'                 # payload.machine_memory
            b'\x00'                 # payload.app_memory
            b'\x00\x00'             # payload.pc_type
            b'\x05'                 # payload.release_month
            b'\x0F'                 # payload.release_day
            b'\x00\x00'             # payload.customer_class
            b'\x00\x00\x00\x00'     # payload.udo_timestamp
            b'\x00\x00'             # payload.dos_ver
            b'\x00\x00'             # payload.session_flags
            b'\x00'                 # payload.video_type
            b'\x00'                 # payload.cpu_type
            b'\x00\x00\x00\x00'     # payload.media_type
            b'\x00\x00\x00\x00'     # payload.win_ver
            b'\x00'                 # payload.win_memory_mode
            b'\x00\x00'             # payload.horizontal_res
            b'\x00\x00'             # payload.vertical_res
            b'\x00\x00'             # payload.num_colors
            b'\x00'                 # payload.filler
            b'\x00\x00'             # payload.region
            b'\x00\x00'             # payload.languages[0]
            b'\x00\x00'             # payload.languages[1]
            b'\x00\x00'             # payload.languages[2]
            b'\x00\x00'             # payload.languages[3]
            b'\x00'                 # payload.connect_speed
        ])
        self.assertEqual(bytes(payload), raw)



# noinspection DuplicatedCode
class V3ClientPacketTestCase(unittest.TestCase):
    def test__init__(self):
        packet = V3ClientPacket(
            packet_type=PacketType.ACK,
            tx_seq=0x20,
            rx_seq=0x30,
            payload=b''
        )
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0x3514)
        self.assertEqual(packet.length, 0x0003)
        self.assertEqual(packet.tx_seq, 0x20)
        self.assertEqual(packet.rx_seq, 0x30)
        self.assertEqual(packet.packet_type, PacketType.ACK)
        self.assertEqual(packet.payload, b'')
        self.assertEqual(packet.msg_end, b'\x0D')

        packet = V3ClientPacket(
            packet_type=PacketType.NAK,
            tx_seq=0x40,
            rx_seq=0x50,
            payload=b'\xDE\xAD\xC0\xDE'
        )
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0xFA3B)
        self.assertEqual(packet.length, 0x0007)
        self.assertEqual(packet.tx_seq, 0x40)
        self.assertEqual(packet.rx_seq, 0x50)
        self.assertEqual(packet.packet_type, PacketType.NAK)
        self.assertEqual(packet.payload, b'\xDE\xAD\xC0\xDE')
        self.assertEqual(packet.msg_end, b'\x0D')

        with self.assertRaises(TypeError):
            # noinspection PyArgumentList
            V3ClientPacket()

        with self.assertRaises(TypeError):
            # noinspection PyArgumentList
            V3ClientPacket(packet_type=0x20)

        with self.assertRaises(TypeError):
            # noinspection PyArgumentList
            V3ClientPacket(packet_type=0x20, tx_seq=0x30)

    def test_is_valid(self):
        packet = V3ClientPacket.from_bytes(
            b'\x5A\xE2\x7E\x00\x04\x17\x1B\xA5\x02\x0D'
        )
        self.assertEqual(packet.is_valid(), True)

        packet = V3ClientPacket.from_bytes(
            b'\x5A\x00\x00\x00\x04\x17\x1B\xA5\x02\x0D'
        )
        self.assertEqual(packet.is_valid(), False)

    def test__bytes__(self):
        packet = V3ClientPacket(
            packet_type=PacketType.ACK,
            tx_seq=0x20,
            rx_seq=0x30,
            payload=b''
        )
        self.assertEqual(
            bytes(packet), b'\x5A\x35\x14\x00\x03\x20\x30\xA4\x0D'
        )

    def test_compute_crc(self):
        packet = V3ClientPacket.from_bytes(
            b'\x5A\xFA\x42\x00\x04\x28\x24\xA5\x02\x0D'
        )
        self.assertEqual(packet.compute_crc(), 0xFA42)

    def test_from_bytes(self):
        packet = V3ClientPacket.from_bytes(
            b'\x5A\xE2\x7E\x00\x04\x17\x1B\xA5\x02\x0D'
        )
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0xE27E)
        self.assertEqual(packet.length, 0x0004)
        self.assertEqual(packet.tx_seq, 0x17)
        self.assertEqual(packet.rx_seq, 0x1B)
        self.assertEqual(packet.packet_type, PacketType.NAK)
        self.assertEqual(packet.payload, b'\x02')
        self.assertEqual(packet.msg_end, b'\x0D')

        with self.assertRaises(ValueError):
            V3ClientPacket.from_bytes(b'')

        with self.assertRaises(ValueError):
            V3ClientPacket.from_bytes(b'\x00' * 8)


# noinspection DuplicatedCode
class V3ServerPacketTestCase(unittest.TestCase):
    def test__init__(self):
        packet = V3ServerPacket(
            packet_type=PacketType.ACK,
            tx_seq=0x20,
            rx_seq=0x30,
            payload=b''
        )
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0x9515)
        self.assertEqual(packet.length, 0x0003)
        self.assertEqual(packet.tx_seq, 0x20)
        self.assertEqual(packet.rx_seq, 0x30)
        self.assertEqual(packet.packet_type, PacketType.ACK)
        self.assertEqual(packet.payload, b'')
        self.assertEqual(packet.msg_end, b'\x0D')

        packet = V3ServerPacket(
            packet_type=PacketType.NAK,
            tx_seq=0x40,
            rx_seq=0x50,
            payload=b'\xDE\xAD\xC0\xDE'
        )
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0x243A)
        self.assertEqual(packet.length, 0x0007)
        self.assertEqual(packet.tx_seq, 0x40)
        self.assertEqual(packet.rx_seq, 0x50)
        self.assertEqual(packet.packet_type, PacketType.NAK)
        self.assertEqual(packet.payload, b'\xDE\xAD\xC0\xDE')
        self.assertEqual(packet.msg_end, b'\x0D')

        with self.assertRaises(TypeError):
            # noinspection PyArgumentList
            V3ServerPacket()

        with self.assertRaises(TypeError):
            # noinspection PyArgumentList
            V3ServerPacket(packet_type=0x20)

        with self.assertRaises(TypeError):
            # noinspection PyArgumentList
            V3ServerPacket(packet_type=0x20, tx_seq=0x30)

    def test_is_valid(self):
        packet = V3ServerPacket.from_bytes(
            b'\x5A\x22\x1F\x00\x04\x17\x1B\x25\x02\x0D'
        )
        self.assertEqual(packet.is_valid(), True)

        packet = V3ServerPacket.from_bytes(
            b'\x5A\x00\x00\x00\x05\x17\x1B\x25\x02\x0D'
        )
        self.assertEqual(packet.is_valid(), False)

    def test__bytes__(self):
        packet = V3ServerPacket(
            packet_type=PacketType.ACK,
            tx_seq=0x20,
            rx_seq=0x30,
            payload=b''
        )
        self.assertEqual(
            bytes(packet), b'\x5A\x95\x15\x00\x03\x20\x30\x24\x0D'
        )

    def test_compute_crc(self):
        packet = V3ServerPacket.from_bytes(
            b'\x5A\xB7\x11\x00\x03\x7F\x7F\x24\x0D'
        )
        self.assertEqual(packet.compute_crc(), 0xB711)

    def test_from_bytes(self):
        packet = V3ServerPacket.from_bytes(
            b'\x5A\xE2\x7E\x00\x04\x17\x1B\x25\x02\x0D'
        )
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0xE27E)
        self.assertEqual(packet.length, 0x0004)
        self.assertEqual(packet.tx_seq, 0x17)
        self.assertEqual(packet.rx_seq, 0x1B)
        self.assertEqual(packet.packet_type, PacketType.NAK)
        self.assertEqual(packet.payload, b'\x02')
        self.assertEqual(packet.msg_end, b'\x0D')

        with self.assertRaises(ValueError):
            V3ServerPacket.from_bytes(b'')

        with self.assertRaises(ValueError):
            V3ServerPacket.from_bytes(b'\x00' * 8)


# noinspection DuplicatedCode,PyUnresolvedReferences
class V3PacketFactoryTestCase(unittest.TestCase):
    def test_client_packet(self):
        packet = V3PacketFactory.client_packet(
            packet_type=PacketType.ACK,
            tx_seq=0x20,
            rx_seq=0x30
        )
        self.assertTrue(isinstance(packet, ClientPacket))
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0x3514)
        self.assertEqual(packet.length, 0x03)
        self.assertEqual(packet.tx_seq, 0x20)
        self.assertEqual(packet.rx_seq, 0x30)
        self.assertEqual(packet.payload, b'')
        self.assertEqual(packet.msg_end, b'\x0D')

        packet = V3PacketFactory.client_packet(
            packet_type=PacketType.ACK,
            tx_seq=0x20,
            rx_seq=0x30,
            payload=b'\xDE\xAD\xC0\xDE'
        )
        self.assertTrue(isinstance(packet, ClientPacket))
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0x9C6F)
        self.assertEqual(packet.length, 0x07)
        self.assertEqual(packet.tx_seq, 0x20)
        self.assertEqual(packet.rx_seq, 0x30)
        self.assertEqual(packet.payload, b'\xDE\xAD\xC0\xDE')
        self.assertEqual(packet.msg_end, b'\x0D')

    def test_server_packet(self):
        packet = V3PacketFactory.server_packet(
            packet_type=PacketType.ACK,
            tx_seq=0x20,
            rx_seq=0x30
        )
        self.assertTrue(isinstance(packet, ServerPacket))
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0x9515)
        self.assertEqual(packet.length, 0x03)
        self.assertEqual(packet.tx_seq, 0x20)
        self.assertEqual(packet.rx_seq, 0x30)
        self.assertEqual(packet.payload, b'')
        self.assertEqual(packet.msg_end, b'\x0D')

        packet = V3PacketFactory.server_packet(
            packet_type=PacketType.ACK,
            tx_seq=0x20,
            rx_seq=0x30,
            payload=b'\xDE\xAD\xC0\xDE'
        )
        self.assertTrue(isinstance(packet, ServerPacket))
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0x426E)
        self.assertEqual(packet.length, 0x07)
        self.assertEqual(packet.tx_seq, 0x20)
        self.assertEqual(packet.rx_seq, 0x30)
        self.assertEqual(packet.payload, b'\xDE\xAD\xC0\xDE')
        self.assertEqual(packet.msg_end, b'\x0D')

    def test_client_packet_from_bytes(self):
        packet = V3PacketFactory.client_packet_from_bytes(
            b'\x5A\x01\x02\x00\x03\x10\x20\xA0\x0D'
        )
        self.assertTrue(isinstance(packet, ClientPacket))
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0x0102)
        self.assertEqual(packet.length, 0x0003)
        self.assertEqual(packet.tx_seq, 0x10)
        self.assertEqual(packet.rx_seq, 0x20)
        self.assertEqual(packet.packet_type, PacketType.DATA)
        self.assertEqual(packet.payload, b'')
        self.assertEqual(packet.msg_end, b'\x0D')

        packet = V3PacketFactory.client_packet_from_bytes(
            b'\x5A\x01\x02\x00\x07\x10\x20\xA0\xDE\xAD\xC0\xDE\x0D'
        )
        self.assertTrue(isinstance(packet, ClientPacket))
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0x0102)
        self.assertEqual(packet.length, 0x0007)
        self.assertEqual(packet.tx_seq, 0x10)
        self.assertEqual(packet.rx_seq, 0x20)
        self.assertEqual(packet.packet_type, PacketType.DATA)
        self.assertEqual(packet.payload, b'\xDE\xAD\xC0\xDE')
        self.assertEqual(packet.msg_end, b'\x0D')

    def test_server_packet_from_bytes(self):
        packet = V3PacketFactory.server_packet_from_bytes(
            b'\x5A\x01\x02\x00\x03\x10\x20\x20\x0D'
        )
        self.assertTrue(isinstance(packet, ServerPacket))
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0x0102)
        self.assertEqual(packet.length, 0x0003)
        self.assertEqual(packet.tx_seq, 0x10)
        self.assertEqual(packet.rx_seq, 0x20)
        self.assertEqual(packet.packet_type, PacketType.DATA)
        self.assertEqual(packet.payload, b'')
        self.assertEqual(packet.msg_end, b'\x0D')

        packet = V3PacketFactory.server_packet_from_bytes(
            b'\x5A\x01\x02\x00\x07\x10\x20\x20\xDE\xAD\xC0\xDE\x0D'
        )
        self.assertTrue(isinstance(packet, ServerPacket))
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0x0102)
        self.assertEqual(packet.length, 0x0007)
        self.assertEqual(packet.tx_seq, 0x10)
        self.assertEqual(packet.rx_seq, 0x20)
        self.assertEqual(packet.packet_type, PacketType.DATA)
        self.assertEqual(packet.payload, b'\xDE\xAD\xC0\xDE')
        self.assertEqual(packet.msg_end, b'\x0D')

    def test_client_data_packet(self):
        packet = V3PacketFactory.client_data_packet(
            tx_seq=0x30,
            rx_seq=0x40,
            token=b'??',
            data=b''
        )
        self.assertTrue(isinstance(packet, ClientPacket))
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0x5304)
        self.assertEqual(packet.length, 0x0005)
        self.assertEqual(packet.tx_seq, 0x30)
        self.assertEqual(packet.rx_seq, 0x40)
        self.assertEqual(packet.packet_type, PacketType.DATA)
        self.assertEqual(packet.payload.token, b'??')
        self.assertEqual(packet.payload.data, b'')
        self.assertEqual(packet.msg_end, b'\x0D')

        packet = V3PacketFactory.client_data_packet(
            tx_seq=0x40,
            rx_seq=0x50,
            token=b'??',
            data=b'\xDE\xAD\xC0\xDE'
        )
        self.assertTrue(isinstance(packet, ClientPacket))
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0x412E)
        self.assertEqual(packet.length, 0x0009)
        self.assertEqual(packet.tx_seq, 0x40)
        self.assertEqual(packet.rx_seq, 0x50)
        self.assertEqual(packet.packet_type, PacketType.DATA)
        self.assertEqual(packet.payload.token, b'??')
        self.assertEqual(packet.payload.data, b'\xDE\xAD\xC0\xDE')
        self.assertEqual(packet.msg_end, b'\x0D')

    def test_server_data_packet(self):
        packet = V3PacketFactory.server_data_packet(
            tx_seq=0x50,
            rx_seq=0x60,
            token=b'XX',
            data=b''
        )
        self.assertTrue(isinstance(packet, ServerPacket))
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0xA9E5)
        self.assertEqual(packet.length, 0x0005)
        self.assertEqual(packet.tx_seq, 0x50)
        self.assertEqual(packet.rx_seq, 0x60)
        self.assertEqual(packet.packet_type, PacketType.DATA)
        self.assertEqual(packet.payload.token, b'XX')
        self.assertEqual(packet.payload.data, b'')
        self.assertEqual(packet.msg_end, b'\x0D')

        packet = V3PacketFactory.server_data_packet(
            tx_seq=0x60,
            rx_seq=0x70,
            token=b'XX',
            data=b'\xDE\xAD\xC0\xDE'
        )
        self.assertTrue(isinstance(packet, ServerPacket))
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0x8F09)
        self.assertEqual(packet.length, 0x0009)
        self.assertEqual(packet.tx_seq, 0x60)
        self.assertEqual(packet.rx_seq, 0x70)
        self.assertEqual(packet.packet_type, PacketType.DATA)
        self.assertEqual(packet.payload.token, b'XX')
        self.assertEqual(packet.payload.data, b'\xDE\xAD\xC0\xDE')
        self.assertEqual(packet.msg_end, b'\x0D')

    def test_client_ack_packet(self):
        packet = V3PacketFactory.client_ack_packet(tx_seq=0x10, rx_seq=0x20)
        self.assertTrue(isinstance(packet, ClientPacket))
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0xFA19)
        self.assertEqual(packet.length, 0x0003)
        self.assertEqual(packet.tx_seq, 0x10)
        self.assertEqual(packet.rx_seq, 0x20)
        self.assertEqual(packet.packet_type, PacketType.ACK)
        self.assertEqual(packet.payload, b'')
        self.assertEqual(packet.msg_end, b'\x0D')

    def test_server_ack_packet(self):
        packet = V3PacketFactory.server_ack_packet(tx_seq=0x30, rx_seq=0x40)
        self.assertTrue(isinstance(packet, ServerPacket))
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0x9031)
        self.assertEqual(packet.length, 0x0003)
        self.assertEqual(packet.tx_seq, 0x30)
        self.assertEqual(packet.rx_seq, 0x40)
        self.assertEqual(packet.packet_type, PacketType.ACK)
        self.assertEqual(packet.payload, b'')
        self.assertEqual(packet.msg_end, b'\x0D')

    def test_client_nak_packet(self):
        packet = V3PacketFactory.client_nak_packet(
            tx_seq=0x60,
            rx_seq=0x70,
            nak_err=NakError.SEQ
        )
        self.assertTrue(isinstance(packet, ClientPacket))
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0x8A14)
        self.assertEqual(packet.length, 0x0004)
        self.assertEqual(packet.tx_seq, 0x60)
        self.assertEqual(packet.rx_seq, 0x70)
        self.assertEqual(packet.packet_type, PacketType.NAK)
        self.assertEqual(packet.payload, b'\x02')
        self.assertEqual(packet.msg_end, b'\x0D')

    def test_server_nak_packet(self):
        packet = V3PacketFactory.server_nak_packet(
            tx_seq=0x70,
            rx_seq=0x80,
            nak_err=NakError.CRC
        )
        self.assertTrue(isinstance(packet, ServerPacket))
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0xB831)
        self.assertEqual(packet.length, 0x0004)
        self.assertEqual(packet.tx_seq, 0x70)
        self.assertEqual(packet.rx_seq, 0x80)
        self.assertEqual(packet.packet_type, PacketType.NAK)
        self.assertEqual(packet.payload, b'\x01')
        self.assertEqual(packet.msg_end, b'\x0D')

    def test_client_heartbeat_packet(self):
        packet = V3PacketFactory.client_heartbeat_packet(
            tx_seq=0x80,
            rx_seq=0x90
        )
        self.assertTrue(isinstance(packet, ClientPacket))
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0xD6ED)
        self.assertEqual(packet.length, 0x0003)
        self.assertEqual(packet.tx_seq, 0x80)
        self.assertEqual(packet.rx_seq, 0x90)
        self.assertEqual(packet.packet_type, PacketType.HEARTBEAT)
        self.assertEqual(packet.payload, b'')
        self.assertEqual(packet.msg_end, b'\x0D')

    def test_server_heartbeat_packet(self):
        packet = V3PacketFactory.client_heartbeat_packet(
            tx_seq=0x90,
            rx_seq=0xA0
        )
        self.assertTrue(isinstance(packet, ClientPacket))
        self.assertEqual(packet.sync, 0x5A)
        self.assertEqual(packet.crc, 0x13F8)
        self.assertEqual(packet.length, 0x0003)
        self.assertEqual(packet.tx_seq, 0x90)
        self.assertEqual(packet.rx_seq, 0xa0)
        self.assertEqual(packet.packet_type, PacketType.HEARTBEAT)
        self.assertEqual(packet.payload, b'')
        self.assertEqual(packet.msg_end, b'\x0D')

    def test_data_payload(self):
        payload = V3PacketFactory.data_payload(token=b'XX', data=b'')
        self.assertTrue(isinstance(payload, DataPayload))
        self.assertEqual(payload.token, b'XX')
        self.assertEqual(payload.data, b'')

        payload = V3PacketFactory.data_payload(token=b'??', data=b'\xAA')
        self.assertTrue(isinstance(payload, DataPayload))
        self.assertEqual(payload.token, b'??')
        self.assertEqual(payload.data, b'\xAA')

    def test_data_payload_from_bytes(self):
        payload = V3PacketFactory.data_payload_from_bytes(b'xG')
        self.assertTrue(isinstance(payload, DataPayload))
        self.assertEqual(payload.token, b'xG')
        self.assertEqual(payload.data, b'')

        payload = V3PacketFactory.data_payload_from_bytes(
            b'aT\x20\x01\x21\x12'
        )
        self.assertTrue(isinstance(payload, DataPayload))
        self.assertEqual(payload.token, b'aT')
        self.assertEqual(payload.data, b'\x20\x01\x21\x12')

    def test_init_payload(self):
        payload = V3PacketFactory.init_payload()
        self.assertTrue(isinstance(payload, V3InitPayload))
        self.assertEqual(payload.platform, 0x03)
        self.assertEqual(payload.major_ver, 0x6E)
        self.assertEqual(payload.minor_ver, 0x5F)
        self.assertEqual(payload.unused, 0x00)
        self.assertEqual(payload.machine_memory, 0x10)
        self.assertEqual(payload.app_memory, 0x00)
        self.assertEqual(payload.pc_type, 0x0000)
        self.assertEqual(payload.release_month, 0x05)
        self.assertEqual(payload.release_day, 0x0F)
        self.assertEqual(payload.customer_class, 0x00)
        self.assertEqual(payload.udo_timestamp, 0x00000000)
        self.assertEqual(payload.dos_ver, 0x0000)
        self.assertEqual(payload.session_flags, 0x0000)
        self.assertEqual(payload.video_type, 0x00)
        self.assertEqual(payload.cpu_type, 0x00)
        self.assertEqual(payload.media_type, 0x00000000)
        self.assertEqual(payload.win_ver, 0x00000000)
        self.assertEqual(payload.win_memory_mode, 0x00)
        self.assertEqual(payload.horizontal_res, 0x0000)
        self.assertEqual(payload.vertical_res, 0x0000)
        self.assertEqual(payload.num_colors, 0x0000)
        self.assertEqual(payload.filler, 0x00)
        self.assertEqual(payload.region, 0x0000)
        self.assertEqual(payload.languages, [0x0000] * 4)
        self.assertEqual(payload.connect_speed, 0x00)

    def test_init_payload_from_bytes(self):
        raw = b''.join([
            b'\x03'                 # payload.platform
            b'\x6E'                 # payload.major_ver
            b'\x5F'                 # payload.minor_ver
            b'\x00'                 # payload.unused
            b'\x10'                 # payload.machine_memory
            b'\x00'                 # payload.app_memory
            b'\x00\x00'             # payload.pc_type
            b'\x05'                 # payload.release_month
            b'\x0F'                 # payload.release_day
            b'\x00\x00'             # payload.customer_class
            b'\x1C\x98\x0B\x3A'     # payload.udo_timestamp
            b'\xC3\xB6'             # payload.dos_ver
            b'\x10\xC0'             # payload.session_flags
            b'\x03'                 # payload.video_type
            b'\x03'                 # payload.cpu_type
            b'\x00\x00\x00\x00'     # payload.media_type
            b'\x04\x00\x00\x00'     # payload.win_ver
            b'\x01'                 # payload.win_memory_mode
            b'\xC0\x06'             # payload.horizontal_res
            b'\x5D\x04'             # payload.vertical_res
            b'\xFF\xFF'             # payload.num_colors
            b'\x00'                 # payload.filler
            b'\x00\x00'             # payload.region
            b'\x00\x00'             # payload.languages[0]
            b'\x00\x00'             # payload.languages[1]
            b'\x00\x00'             # payload.languages[2]
            b'\x00\x00'             # payload.languages[3]
            b'\x02'                 # payload.connect_speed
        ])
        payload = V3PacketFactory.init_payload_from_bytes(raw)

        self.assertTrue(isinstance(payload, V3InitPayload))
        self.assertEqual(payload.platform, 0x03)
        self.assertEqual(payload.major_ver, 0x6E)
        self.assertEqual(payload.minor_ver, 0x5F)
        self.assertEqual(payload.unused, 0x00)
        self.assertEqual(payload.machine_memory, 0x10)
        self.assertEqual(payload.app_memory, 0x00)
        self.assertEqual(payload.pc_type, 0x00)
        self.assertEqual(payload.release_month, 0x05)
        self.assertEqual(payload.release_day, 0x0F)
        self.assertEqual(payload.customer_class, 0x0000)
        self.assertEqual(payload.udo_timestamp, 0x1C980B3A)
        self.assertEqual(payload.dos_ver, 0xC3B6)
        self.assertEqual(payload.session_flags, 0x10C0)
        self.assertEqual(payload.video_type, 0x03)
        self.assertEqual(payload.cpu_type, 0x03)
        self.assertEqual(payload.media_type, 0x00000000)
        self.assertEqual(payload.win_ver, 0x04000000)
        self.assertEqual(payload.win_memory_mode, 0x01)
        self.assertEqual(payload.horizontal_res, 0xC006)
        self.assertEqual(payload.vertical_res, 0x5D04)
        self.assertEqual(payload.num_colors, 0xFFFF)
        self.assertEqual(payload.filler, 0x00)
        self.assertEqual(payload.region, 0x0000)
        self.assertEqual(payload.languages, [0x0000] * 4)
        self.assertEqual(payload.connect_speed, 0x02)
