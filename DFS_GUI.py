import os
from pathlib import Path
from tkinter import Tk, Menu, Button, Label, filedialog, Y, LEFT
from tkinter.filedialog import askopenfilename
from tkinter.ttk import Combobox, Treeview
from webbrowser import open_new

from PyAcornDFS import acorn_dfs


def get_file(ext='ssd', title="Select file"):
    return filedialog.askopenfilename(
        initialdir=os.getcwd(),
#        initialdir=Path.home(),
        title=title,
        filetypes=((f"DFS files", "*.ssd *.mmb"), ("all files", "*.*")),
    )


def About():
    open_new("https://github.com/fordp2002/PyAcornDFS")


class dfs_gui(acorn_dfs):
    ''' GUI for Acorn DFS '''

    def __init__(self):
        self.root = Tk()
        self.root.title("Acorn DFS")
        self.root.geometry("1024x768")
        # root.iconbitmap(bitmap=os.path.join(os.path.dirname(__file__), 'Owl.ico'))
        # dfs = acorn_dfs("ROMs1.ssd")

        self.make_menu()
        self.tree = self.make_tree()

        # icons = get_icons()
        # for index, info in enumerate(devices):
        #    add_device(index, info)
        self.root.mainloop()

    def Open(self):
        ''' Get a new file to process '''
        name = get_file()
        self.change_file(name)

    def Close(self):
        ''' Close the file '''
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
        ''' Return selected nodes '''
        self.root.config(cursor="wait")
        self.root.update()
        return self.tree.selection()

    def save(self):
        ''' Save node(s) '''
        for node in self.get_selection():
            index = node.split()
            temp = len(index)
            if temp == 1:
                self.write_ssd(int(index[0]))
            elif temp == 2:
                self.write_file(int(index[0]), int(index[1]))
        self.root.config(cursor="")

    def make_menu(self):
        ''' Menu Bar '''
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
        ''' Popup Menu '''
        self.popup = Menu(self.root, tearoff=0)
        self.popup.add_command(label="Save", command=self.save)

    def make_tree(self):
        ''' Build a Tree '''

        def do_popup(event):
            ''' Bring up Pop Up menu '''
            if self.tree.focus() is not None:
                self.popup.post(event.x_root, event.y_root)

        tree = Treeview(self.root)
        tree["columns"] = ('Start', 'Execute', 'Length', 'Sector')
        tree.column("#0", width=350)
        tree.column("Start", width=70)
        tree.column("Execute", width=70)
        tree.column("Length", width=70)
        tree.column("Sector", width=70)
        tree.heading("Start", text="Start &")
        tree.heading("Execute", text="Execute &")
        tree.heading("Length", text="Length")
        tree.heading("Sector", text="Sector")
        self.make_popup(tree)
        tree.bind("<Button-3>", do_popup)
        tree.pack(fill=Y, side=LEFT)
        return tree

    def change_file(self, filename=None):
        ''' Add a device to the tree '''
        for child in self.tree.get_children():
            self.tree.delete(child)
        self.open_image(filename)
        if self.disk_info:
            for disk_index, disk in enumerate(self.disk_info):
                if disk:
                    detail = f"Contains {disk['file_count']} file(s)"
                    dev = self.tree.insert("", "end", [disk_index], text=f"Disk {disk_index}: {disk['title']}", values=detail)
                    for file_index, info in enumerate(disk['file_info']):
                        columns = (
                            f"{info['load_&']:08X}",
                            f"{info['exec_&']:08X}",
                            f"{info['size']:06X}",
                            f"{info['start']:03X}",
                        )
                        self.tree.insert(
                            dev, "end", [disk_index, file_index], text=info['name'], values=columns
                        )


dfs_gui()
