import unittest

from pyol.gid import GlobalId


class TestGlobalId(unittest.TestCase):
    def test__init__(self):
        gid = GlobalId(parts=(0xDEAD, 0xC0DE))
        self.assertEqual(gid._gid, 0xDEADC0DE)

        gid = GlobalId(parts=(0xDE, 0xAD, 0xC0DE))
        self.assertEqual(gid._gid, 0xDEADC0DE)

        gid = GlobalId(int=0xDEADC0DE)
        self.assertEqual(gid._gid, 0xDEADC0DE)

        gid = GlobalId(bytes=b'\xDE\xAD\xC0\xDE')
        self.assertEqual(gid._gid, 0xDEADC0DE)

        with self.assertRaises(TypeError):
            GlobalId()
            GlobalId(fails=())

        with self.assertRaises(ValueError):
            GlobalId(parts=())
            GlobalId(parts=(1, 2, 3, 4))
            GlobalId(parts=(0xFFFFFF, 1))
            GlobalId(parts=(1, 0xFFFFF))
            GlobalId(parts=(0xFFFF, 1, 1))
            GlobalId(parts=(1, 0xFFFF, 1))
            GlobalId(parts=(1, 1, 0xFFFFFF))
            GlobalId(int=0xFFFFFFFFFFFF)

    def test__int__(self):
        gid = GlobalId(int=0xDEADC0DE)
        self.assertEqual(int(gid), 0xDEADC0DE)

    def test__bytes__(self):
        gid = GlobalId(int=0xDEADC0DE)
        self.assertEqual(bytes(gid), b'\xDE\xAD\xC0\xDE')

    def test_gid(self):
        gid = GlobalId(int=0xDEADC0DE)
        self.assertEqual(gid.gid, 0xDEADC0DE)

    def test_w1(self):
        gid = GlobalId(int=0xDEADC0DE)
        self.assertEqual(gid.w1, 0xDEAD)

        gid.w1 = 0xC0DE
        self.assertEqual(gid.w1, 0xC0DE)
        self.assertEqual(gid.gid, 0xC0DEC0DE)

    def test_w2(self):
        gid = GlobalId(int=0xDEADC0DE)
        self.assertEqual(gid.w2, 0xC0DE)

        gid.w2 = 0xDEAD
        self.assertEqual(gid.w2, 0xDEAD)
        self.assertEqual(gid.gid, 0xDEADDEAD)

    def test_b1(self):
        gid = GlobalId(int=0xDEADC0DE)
        self.assertEqual(gid.b1, 0xDE)

        gid.b1 = 0xAA
        self.assertEqual(gid.b1, 0xAA)
        self.assertEqual(gid.gid, 0xAAADC0DE)

    def test_b2(self):
        gid = GlobalId(int=0xDEADC0DE)
        self.assertEqual(gid.b2, 0xAD)

        gid.b2 = 0xAA
        self.assertEqual(gid.b2, 0xAA)
        self.assertEqual(gid.gid, 0xDEAAC0DE)

    def test__repr__(self):
        gid = GlobalId(int=0xDEADC0DE)
        self.assertEqual(repr(gid), '57005-49374')

    def test__str__(self):
        gid = GlobalId(int=0xDEADC0DE)
        self.assertEqual(str(gid), '57005-49374')

    def test_str2(self):
        gid = GlobalId(int=0xDEADC0DE)
        self.assertEqual(gid.str2(), '57005-49374')

    def test_str3(self):
        gid = GlobalId(int=0xDEADC0DE)
        self.assertEqual(gid.str3(), '222-173-49374')

    def test_from_str(self):
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