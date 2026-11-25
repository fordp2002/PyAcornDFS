import os
import struct
import tempfile
import unittest
from types import SimpleNamespace

from pyacorndfs.gui import dfs_gui
from pyacorndfs.wx_gui import DfsFrame
from pyacorndfs.dfs import DISK_SIZE, acorn_dfs


def make_ssd(path):
    data = bytearray(DISK_SIZE)
    data[:8] = b"TEST    "
    struct.pack_into("4sBBBB", data, 256, b"    ", 0, 8, 3, 0x20)
    struct.pack_into("7sB", data, 8, b"FILE   ", ord("$"))
    struct.pack_into("HHHBB", data, 264, 0, 0, 4, 0, 2)
    data[2 * 256 : 2 * 256 + 4] = b"DATA"
    with open(path, "wb") as file_p:
        file_p.write(data)


class TkTree:
    def __init__(self):
        self.children = []
        self.expanded = []
        self.inserted = []

    def get_children(self):
        return self.children

    def delete(self, item):
        self.children.remove(item)

    def insert(self, _parent, _index, _iid, **kwargs):
        item = str(len(self.inserted))
        self.inserted.append((item, kwargs))
        self.children.append(item)
        return item

    def item(self, item, **kwargs):
        if kwargs.get("open"):
            self.expanded.append(item)


class WxTree:
    def __init__(self):
        self.expanded = []
        self.inserted = []

    def DeleteAllItems(self):
        self.inserted.clear()

    def GetRootItem(self):
        return "root"

    def AppendItem(self, _parent, text, data=None):
        item = str(len(self.inserted))
        self.inserted.append((item, text, data))
        return item

    def SetItemText(self, _item, _column, _value):
        pass

    def Expand(self, item):
        self.expanded.append(item)


class GuiTreeExpandTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.ssd_path = os.path.join(self.directory.name, "test.ssd")
        make_ssd(self.ssd_path)

    def tearDown(self):
        self.directory.cleanup()

    def _tk_gui(self, disk_info=None):
        gui = object.__new__(dfs_gui)
        gui.tree = TkTree()
        gui.set_title = lambda _text: None
        if disk_info is not None:
            gui.disk_info = disk_info
        return gui

    def _wx_gui(self, disk=None):
        return SimpleNamespace(
            tree=WxTree(),
            disk=disk or acorn_dfs(),
            SetTitle=lambda _title: None,
        )

    def test_initial_single_ssd_expands_in_both_guis(self):
        tk_gui = self._tk_gui()
        tk_gui.change_file(self.ssd_path)
        self.assertEqual(len(tk_gui.tree.expanded), 1)
        self.assertEqual(len(tk_gui.tree.inserted), 2)

        wx_gui = self._wx_gui()
        self.assertTrue(DfsFrame.change_file(wx_gui, self.ssd_path))
        self.assertEqual(len(wx_gui.tree.expanded), 1)
        self.assertEqual(len(wx_gui.tree.inserted), 2)

    def test_replacing_an_open_image_does_not_expand_in_both_guis(self):
        existing_disk = acorn_dfs(self.ssd_path)

        tk_gui = self._tk_gui(existing_disk.disk_info)
        tk_gui.change_file(self.ssd_path)
        self.assertEqual(tk_gui.tree.expanded, [])

        wx_gui = self._wx_gui(existing_disk)
        self.assertTrue(DfsFrame.change_file(wx_gui, self.ssd_path))
        self.assertEqual(wx_gui.tree.expanded, [])


if __name__ == "__main__":
    unittest.main()
