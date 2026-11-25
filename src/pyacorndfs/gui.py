from logging import root
import os
import sys
from pathlib import Path
from tkinter import (
    Menu,
    Button,
    Label,
    filedialog,
    Y,
    LEFT,
    Canvas,
    PhotoImage,
    messagebox,
)
from tkinter.filedialog import askopenfilename
from tkinter.ttk import Combobox, Treeview
from tkinterdnd2 import DND_FILES, TkinterDnD
from webbrowser import open_new

# from configparser import ConfigParser

from . import disasm
from .dfs import acorn_dfs


def get_file(ext="ssd", title="Select file"):
    return filedialog.askopenfilename(
        initialdir=os.getcwd(),
        #        initialdir=Path.home(),
        title=title,
        filetypes=(
            (f"DFS files", "*.ssd *.SSD *.dsd *.DSD *.mmb *.MMB"),
            ("all files", "*.*"),
        ),
    )


def About():
    open_new("https://github.com/fordp2002/PyAcornDFS")


class dfs_gui(acorn_dfs):
    """GUI for Acorn DFS"""

    def __init__(self, filename=None):
        self.root = TkinterDnD.Tk()
        self.set_title()
        self.root.geometry("1024x768")
        icon = PhotoImage(
            file=os.path.join(os.path.dirname(__file__), "dfs_floppy.png")
        )
        self.root.iconphoto(False, icon)
        self.make_menu()
        self.tree = self.make_tree()
        if filename:
            self.change_file(filename)
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self.on_drop)
        # icons = get_icons()
        self.cursor = "wait" if os.name == "nt" else "clock"
        self.root.mainloop()

    def set_title(self, text=""):
        """Change the title"""
        if text:
            text += " - "
        self.root.title(f"{text}Acorn DFS ")

    def show_screen(self, data):
        """Show Mode Zero Screen for Debug"""
        if data:
            height, _mod = divmod(len(data), 80)
            if height >= 1:
                x = 0
                y = 0
                self.window = Canvas(self.root, width=640, height=height)
                self.window.pack()
                for value in data:
                    for offset in range(8):
                        if value & (1 << (7 - offset)):
                            self.window.create_line(x, y, x + 1, y)
                            # self.window.create_rectangle((x, y) * 2)
                        x += 1
                    if x == 640:
                        x = 0
                        y += 1

    def Open(self):
        """Get a new file to process"""
        name = get_file()
        self.change_file(name)

    def add_file(self, filename):
        """add a file to a disk"""
        result = False
        for node in self.get_selection():
            index = node.split()
            temp = len(index)
            if temp == 1:
                result = self.add_file(filename)
        self.root.config(cursor="")
        return

    def on_drop(self, event):
        """Open one dropped DFS image."""
        filenames = self.root.tk.splitlist(event.data)
        if not filenames:
            return
        if len(filenames) != 1:
            messagebox.showerror(
                "Open disk image",
                "Please drop one disk image at a time.",
                parent=self.root,
            )
            return
        filename = filenames[0]
        if Path(filename).suffix.lower() in (".ssd", ".dsd", ".mmb"):
            self.change_file(filename)
        else:
            if not self.add_file(self, filename):
                messagebox.showerror(
                    "File not added",
                    "Please drop a suitable file.",
                    parent=self.root,
                )

    def Close(self):
        """Close the file"""
        self.change_file()  # Just open an empty file!

    def NewMMB(self):
        _name = askopenfilename()
        print("New File!")
        self.change_file()  # Just open an empty file!

    def NewSSD(self):
        _name = askopenfilename()
        print("New File!")
        self.change_file()  # Just open an empty file!

    def get_selection(self):
        """Return selected nodes"""
        self.root.config(cursor=self.cursor)
        self.root.update()
        return self.tree.selection()
        # return [node.split() for node in self.tree.selection()]

    def save(self):
        """Save node(s)"""
        for node in self.get_selection():
            index = node.split()
            temp = len(index)
            if temp == 1:
                self.write_ssd(int(index[0]))
            elif temp == 2:
                self.write_file(int(index[0]), int(index[1]))
        self.root.config(cursor="")

    def save_dsd(self):
        """Save dsd images"""
        for node in self.get_selection():
            index = node.split()
            temp = len(index)
            if temp == 1:
                self.write_dsd(int(index[0]))
        self.root.config(cursor="")

    def basic(self):
        """Extract Basic"""
        for node in self.get_selection():
            index = node.split()
            temp = len(index)
            if temp == 2:
                self.extract_basic(int(index[0]), int(index[1]))
        self.root.config(cursor="")

    def mode_zero(self):
        """Show Image"""
        for node in self.get_selection():
            index = node.split()
            temp = len(index)
            if temp == 2:
                self.show_screen(self.get_data(int(index[0]), int(index[1]))[0])
        self.root.config(cursor="")

    def py8_dis(self):
        """Disassemble file node(s) with py8dis to NAME.6502 next to the image"""
        failures = []
        for node in self.get_selection():
            index = node.split()
            if len(index) == 2:
                try:
                    self.disassemble(int(index[0]), int(index[1]))
                except (disasm.DisasmError, OSError) as error:
                    failures.append(f"{error}\n{getattr(error, 'stderr', '')}".strip())
        self.root.config(cursor="")
        if failures:
            messagebox.showerror("Disassemble", "\n\n".join(failures)[-2000:], parent=self.root)

    def make_menu(self):
        """Menu Bar"""
        self.menu = Menu(self.root)
        self.root.config(menu=self.menu)
        self.filemenu = Menu(self.menu)
        self.menu.add_cascade(label="File", menu=self.filemenu)
        self.filemenu.add_command(label="Open", command=self.Open)
        self.filemenu.add_command(label="Close", command=self.Close)

        # filemenu.add_command(label="Close", command=Close)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="New SSD", command=self.NewSSD)
        self.filemenu.add_command(label="New MMB", command=self.NewMMB)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.root.quit)

        self.helpmenu = Menu(self.menu)
        self.menu.add_cascade(label="Help", menu=self.helpmenu)
        self.helpmenu.add_command(label="About...", command=About)
        # menu(root)

    def make_popup(self, tree):
        """Popup Menu"""
        self.popup = Menu(self.root, tearoff=0)
        self.popup.add_command(label="Save", command=self.save)
        self.popup.add_command(label="Save DSD", command=self.save_dsd)
        self.popup.add_command(label="Extract Basic", command=self.basic)
        self.popup.add_command(label="Mode Zero", command=self.mode_zero)
        self.popup.add_command(
            label="Disassemble",
            command=self.py8_dis,
            state="normal" if disasm.is_available() else "disabled",
        )

    def make_tree(self):
        """Build a Tree"""

        def do_popup(event):
            """Bring up Pop Up menu"""
            if self.tree.focus() is not None:
                self.popup.post(event.x_root, event.y_root)

        tree = Treeview(self.root)
        tree["columns"] = ("Start", "Execute", "Length", "Sector")
        tree.column("#0", width=350)
        col_width = 90
        tree.column("Start", width=col_width)
        tree.column("Execute", width=col_width)
        tree.column("Length", width=col_width)
        tree.column("Sector", width=col_width)
        tree.heading("Start", text="Start &")
        tree.heading("Execute", text="Execute &")
        tree.heading("Length", text="Length")
        tree.heading("Sector", text="Sector")
        self.make_popup(tree)
        tree.bind("<Button-3>", do_popup)
        tree.pack(fill="both", expand=True, side=LEFT)
        return tree

    def change_file(self, filename=None):
        """Add a device to the tree"""
        expand_initial_ssd = (
            not getattr(self, "disk_info", None)
            and filename
            and Path(filename).suffix.lower() == ".ssd"
        )
        for child in self.tree.get_children():
            self.tree.delete(child)
        self.open_image(filename)
        self.set_title(self.filename)
        if self.disk_info:
            for disk_index, disk in enumerate(self.disk_info):
                if disk:
                    detail = f"Contains {disk['file_count']} file(s)"
                    dev = self.tree.insert(
                        "",
                        "end",
                        [disk_index],
                        text=f"Disk {disk_index}: {disk['title']}",
                        values=detail,
                    )
                    if expand_initial_ssd:
                        self.tree.item(dev, open=True)
                    for file_index, info in enumerate(disk["file_info"]):
                        columns = (
                            f"{info['load_&']:08X}",
                            f"{info['exec_&']:08X}",
                            f"{info['size']:06X}",
                            f"{info['start']:03X}",
                        )
                        self.tree.insert(
                            dev,
                            "end",
                            [disk_index, file_index],
                            text=f"{info['ext']}.{info['name']}",
                            values=columns,
                        )


def main(argv=None):
    """Start the GUI, optionally opening a disk image passed on the command line."""
    if argv is None:
        argv = sys.argv[1:]
    dfs_gui(argv[0] if argv else None)


if __name__ == "__main__":
    main()
