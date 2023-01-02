import unittest

from pyol.core.gid import GlobalId


class TestGlobalId(unittest.TestCase):
    def test__init__(self):
        gid = GlobalId(0xDEADC0DE)
        self.assertEqual(gid.gid, 0xDEADC0DE)

        with self.assertRaises(ValueError):
            GlobalId(0xFFFFFFFFFF)
            GlobalId(-1)

    def test__int__(self):
        gid = GlobalId(0xDEADC0DE)
        self.assertEqual(int(gid), 0xDEADC0DE)

    def test__bytes__(self):
        gid = GlobalId(0xDEADC0DE)
        self.assertEqual(bytes(gid), b'\xDE\xAD\xC0\xDE')

    def test_w1(self):
        gid = GlobalId(0xDEADC0DE)
        self.assertEqual(gid.w1, 0xDEAD)

        gid.w1 = 0xC0DE
        self.assertEqual(gid.w1, 0xC0DE)
        self.assertEqual(gid.gid, 0xC0DEC0DE)

        with self.assertRaises(ValueError):
            gid.w1 = 0xDEADC0DE
            gid.w1 = -1

    def test_w2(self):
        gid = GlobalId(0xDEADC0DE)
        self.assertEqual(gid.w2, 0xC0DE)

        gid.w2 = 0xDEAD
        self.assertEqual(gid.w2, 0xDEAD)
        self.assertEqual(gid.gid, 0xDEADDEAD)

        with self.assertRaises(ValueError):
            gid.w2 = 0xDEADC0DE
            gid.w2 = -1

    def test_b1(self):
        gid = GlobalId(0xDEADC0DE)
        self.assertEqual(gid.b1, 0xDE)

        gid.b1 = 0xAA
        self.assertEqual(gid.b1, 0xAA)
        self.assertEqual(gid.gid, 0xAAADC0DE)

        with self.assertRaises(ValueError):
            gid.b1 = 0xFFFF
            gid.b1 = -1

    def test_b2(self):
        gid = GlobalId(0xDEADC0DE)
        self.assertEqual(gid.b2, 0xAD)

        gid.b2 = 0xAA
        self.assertEqual(gid.b2, 0xAA)
        self.assertEqual(gid.gid, 0xDEAAC0DE)

        with self.assertRaises(ValueError):
            gid.b2 = 0xFFFF
            gid.b2 = -1

    def test__repr__(self):
        gid = GlobalId(0xDEADC0DE)
        self.assertEqual(repr(gid), 'GlobalId(gid=3735929054)')

    def test__str__(self):
        gid = GlobalId(0xDEADC0DE)
        self.assertEqual(str(gid), '222-173-49374')

        gid = GlobalId(0x00400020)
        self.assertEqual(str(gid), '64-32')

    def test_from_str(self):
        gid = GlobalId.from_str('3735929054')
        self.assertEqual(gid.gid, 0xDEADC0DE)

        gid = GlobalId.from_str('57005-49374')
        self.assertEqual(gid.gid, 0xDEADC0DE)

        gid = GlobalId.from_str('222-173-49374')
        self.assertEqual(gid.gid, 0xDEADC0DE)

        with self.assertRaises(ValueError):
            GlobalId.from_str('DEADC0DE')
            GlobalId.from_str('99999-1')
            GlobalId.from_str('1-99999')
            GlobalId.from_str('999-1-1')
            GlobalId.from_str('1-999-1')
            GlobalId.from_str('1-1-99999')

    def test_from_tuple(self):
        gid = GlobalId.from_tuple((57005, 49374))
        self.assertEqual(gid.gid, 0xDEADC0DE)

        gid = GlobalId.from_tuple((222, 173, 49374))
        self.assertEqual(gid.gid, 0xDEADC0DE)

        with self.assertRaises(ValueError):
            GlobalId.from_tuple((1,))
            GlobalId.from_tuple((1, 2, 3, 4))
            GlobalId.from_tuple((99999, 1))
            GlobalId.from_tuple((1, 99999))
            GlobalId.from_tuple((999, 1, 1))
            GlobalId.from_tuple((1, 999, 1))
            GlobalId.from_tuple((1, 1, 99999))

    def test_from_bytes(self):
        gid = GlobalId.from_bytes(b'\xDE\xAD\xC0\xDE')
        self.assertEqual(gid.gid, 0xDEADC0DE)

        gid = GlobalId.from_bytes(b'\xDE\xAD\xC0\xDE', byteorder='big')
        self.assertEqual(gid.gid, 0xDEADC0DE)

        gid = GlobalId.from_bytes(b'\xDE\xC0\xAD\xDE', byteorder='little')
        self.assertEqual(gid.gid, 0xDEADC0DE)

        with self.assertRaises(ValueError):
            GlobalId.from_bytes(b'\xC0\xDE')
            GlobalId.from_bytes(b'\xDE\xAD\xC0\xDE\xDE\xAD\xC0\xDE')
            GlobalId.from_Bytes(b'\xDE\xAD\xC0\xDE', byteorder='deadcode')
