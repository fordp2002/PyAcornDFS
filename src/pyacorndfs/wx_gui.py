"""Native-widgets wxPython GUI for browsing Acorn DFS disk images."""

import struct
import sys
from pathlib import Path

import wx
import wx.dataview

from . import disasm
from .dfs import acorn_dfs


DISK_IMAGE_EXTENSIONS = {".ssd", ".dsd", ".mmb"}
FILE_COLUMNS = ("Name", "Start &", "Execute &", "Length", "Sector")


class DiskImageDropTarget(wx.FileDropTarget):
    """Open disk images dropped onto the main window."""

    def __init__(self, frame):
        super().__init__()
        self.frame = frame

    def OnDropFiles(self, _x, _y, filenames):
        if len(filenames) != 1:
            wx.MessageBox(
                "Please drop one disk image at a time.",
                "Open disk image",
                wx.OK | wx.ICON_ERROR,
                self.frame,
            )
            return False
        return self.frame.change_file(filenames[0])


class ModeZeroFrame(wx.Frame):
    """Display file data as a monochrome 640-pixel-wide image."""

    def __init__(self, parent, data):
        height = len(data) // 80
        super().__init__(parent, title="Mode Zero", size=(640, height))
        pixels = bytearray()
        for value in data[: height * 80]:
            for bit in range(7, -1, -1):
                colour = 0 if value & (1 << bit) else 255
                pixels.extend((colour, colour, colour))
        self._pixels = pixels
        bitmap = wx.Bitmap.FromBuffer(640, height, self._pixels)
        panel = wx.Panel(self)
        image = wx.StaticBitmap(panel, bitmap=bitmap)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(image, 0, wx.ALL, 4)
        panel.SetSizerAndFit(sizer)
        self.SetClientSize(panel.GetBestSize())


class DfsFrame(wx.Frame):
    """Window for viewing and extracting files from DFS disk images."""

    def __init__(self):
        wx.Frame.__init__(self, None, title="Acorn DFS", size=(1024, 768))
        self.disk = acorn_dfs()

        self.tree = wx.dataview.TreeListCtrl(
            self,
            style=wx.dataview.TL_DEFAULT_STYLE | wx.dataview.TL_MULTIPLE,
        )
        for title, width in zip(FILE_COLUMNS, (350, 100, 100, 100, 80)):
            self.tree.AppendColumn(title, width=width)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.tree, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self._make_menu()
        self.tree.Bind(
            wx.dataview.EVT_TREELIST_ITEM_CONTEXT_MENU,
            self._on_context_menu,
        )
        self.SetDropTarget(DiskImageDropTarget(self))
        self.tree.SetDropTarget(DiskImageDropTarget(self))

        icon_path = Path(__file__).with_name("dfs_floppy.png")
        if icon_path.is_file():
            icon = wx.Icon(str(icon_path), wx.BITMAP_TYPE_PNG)
            if icon.IsOk():
                self.SetIcon(icon)

    def _make_menu(self):
        menu_bar = wx.MenuBar()
        file_menu = wx.Menu()
        open_item = file_menu.Append(wx.ID_OPEN, "&Open...\tCtrl+O")
        close_item = file_menu.Append(wx.ID_CLOSE, "&Close")
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit")
        menu_bar.Append(file_menu, "&File")

        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT, "&About")
        menu_bar.Append(help_menu, "&Help")
        self.SetMenuBar(menu_bar)

        self.Bind(wx.EVT_MENU, self._on_open, open_item)
        self.Bind(wx.EVT_MENU, self._on_close, close_item)
        self.Bind(wx.EVT_MENU, self._on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self._on_about, about_item)

    def _on_open(self, _event):
        wildcard = (
            "DFS disk images (*.ssd;*.dsd;*.mmb)|*.ssd;*.dsd;*.mmb|"
            "All files (*.*)|*.*"
        )
        with wx.FileDialog(
            self,
            "Open disk image",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE,
        ) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                filenames = dialog.GetPaths()
                if len(filenames) == 1:
                    self.change_file(filenames[0])
                elif len(filenames) == 2 and all(
                    Path(filename).suffix.lower() == ".ssd"
                    for filename in filenames
                ):
                    self.change_file(filenames)
                else:
                    wx.MessageBox(
                        "Open one disk image, or select exactly two SSD images.",
                        "Open disk image",
                        wx.OK | wx.ICON_ERROR,
                        self,
                    )

    def _on_close(self, _event):
        self.change_file()

    def _on_exit(self, _event):
        self.Close()

    def _on_about(self, _event):
        wx.LaunchDefaultBrowser("https://github.com/fordp2002/PyAcornDFS")

    def _on_context_menu(self, event):
        item = event.GetItem()
        if item not in self.tree.GetSelections():
            self.tree.Select(item)

        menu = wx.Menu()
        actions = (
            ("Save", self._save),
            ("Save DSD", self._save_dsd),
            ("Extract BASIC", self._extract_basic),
            ("Mode Zero", self._show_mode_zero),
            ("Disassemble", self._disassemble),
        )
        for title, handler in actions:
            item = menu.Append(wx.ID_ANY, title)
            menu.Bind(wx.EVT_MENU, handler, item)
            if handler == self._disassemble:
                item.Enable(disasm.is_available())
        self.PopupMenu(menu)
        menu.Destroy()

    def change_file(self, filename=None):
        """Load a disk image or an SSD pair and refresh the catalogue."""
        is_pair = isinstance(filename, (list, tuple))
        if is_pair and (
            len(filename) != 2
            or any(Path(path).suffix.lower() != ".ssd" for path in filename)
        ):
            wx.MessageBox(
                "Select exactly two SSD images to open them as a DSD.",
                "Unsupported files",
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return False
        if (
            not is_pair
            and filename
            and Path(filename).suffix.lower() not in DISK_IMAGE_EXTENSIONS
        ):
            wx.MessageBox(
                "Please open an SSD, DSD, or MMB disk image.",
                "Unsupported file",
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return False

        expand_initial_ssd = (
            not self.disk.disk_info
            and not is_pair
            and filename
            and Path(filename).suffix.lower() == ".ssd"
        )

        try:
            if is_pair:
                image = acorn_dfs()
                image.open_ssd_pair(*filename)
            else:
                image = acorn_dfs(filename)
        except (OSError, ValueError, struct.error) as error:
            wx.MessageBox(
                f"Could not open the disk image:\n{error}",
                "Open disk image",
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return False

        self.disk = image
        self.tree.DeleteAllItems()
        root = self.tree.GetRootItem()
        source_filenames = self.disk.source_filenames
        display_filename = (
            " + ".join(Path(path).name for path in source_filenames)
            if len(source_filenames) > 1
            else self.disk.filename
        )
        self.SetTitle(
            f"{display_filename} - Acorn DFS"
            if display_filename
            else "Acorn DFS"
        )

        for disk_index, disk in enumerate(self.disk.disk_info or []):
            if not disk:
                continue
            disk_item = self.tree.AppendItem(
                root,
                f"Disk {disk_index}: {disk['title']} "
                f"({disk['file_count']} file(s))",
                data=(disk_index, None),
            )

            for file_index, info in enumerate(disk["file_info"]):
                file_item = self.tree.AppendItem(
                    disk_item,
                    f"  {info['ext']}.{info['name']}",
                    data=(disk_index, file_index),
                )
                columns = (
                    f"{info['load_&']:08X}",
                    f"{info['exec_&']:08X}",
                    f"{info['size']:06X}",
                    f"{info['start']:03X}",
                )
                for column, value in enumerate(columns, start=1):
                    self.tree.SetItemText(file_item, column, value)
            if expand_initial_ssd:
                self.tree.Expand(disk_item)
        return True

    def _selected_entries(self):
        for item in self.tree.GetSelections():
            yield self.tree.GetItemData(item)

    def _save(self, _event):
        for disk_index, file_index in self._selected_entries():
            if file_index is None:
                self.disk.write_ssd(disk_index)
            else:
                self.disk.write_file(disk_index, file_index)

    def _save_dsd(self, _event):
        for disk_index, file_index in self._selected_entries():
            if file_index is None:
                self.disk.write_dsd(disk_index)

    def _extract_basic(self, _event):
        for disk_index, file_index in self._selected_entries():
            if file_index is not None:
                self.disk.extract_basic(disk_index, file_index)

    def _show_mode_zero(self, _event):
        for disk_index, file_index in self._selected_entries():
            if file_index is None:
                continue
            data = self.disk.get_data(disk_index, file_index)[0]
            if len(data) >= 80:
                ModeZeroFrame(self, data).Show()

    def _disassemble(self, _event):
        """Disassemble file(s) with py8dis to NAME.6502 next to the image"""
        failures = []
        with wx.BusyCursor():
            for disk_index, file_index in self._selected_entries():
                if file_index is not None:
                    try:
                        self.disk.disassemble(disk_index, file_index)
                    except (disasm.DisasmError, OSError) as error:
                        failures.append(f"{error}\n{getattr(error, 'stderr', '')}".strip())
        if failures:
            wx.MessageBox("\n\n".join(failures)[-2000:], "Disassemble", wx.OK | wx.ICON_ERROR, self)


def main(argv=None):
    """Start wxPython and optionally open a disk image passed on the command line."""
    if argv is None:
        argv = sys.argv[1:]
    app = wx.App(False)
    frame = DfsFrame()
    app.SetTopWindow(frame)
    frame.Show()
    if argv:
        frame.change_file(argv[0])
    app.MainLoop()


if __name__ == "__main__":
    main()
