import os
from tkinter import Tk, Menu, Button, Label, filedialog, Y, LEFT
from tkinter.filedialog import askopenfilename
from tkinter.ttk import Combobox, Treeview
from webbrowser import open_new

from PyAcornDFS import acorn_dfs


def get_file(ext='ssd', title="Select file"):
    return filedialog.askopenfilename(
        initialdir=os.getcwd(),
        title=title,
        filetypes=((f"{ext} files", f"*.{ext}"), ("all files", "*.*")),
    )


def Open():
    name = askopenfilename()
    print(name)


def NewMMB():
    print("New File!")


def NewSSD():
    print("New File!")


def About():
    open_new("https://github.com/fordp2002/PyAcornDFS")


class Popup:
    ''' Popup Menu '''
    def __init__(self, root, tree):
        ''' Contructor '''
        self.root = root
        self.tree = tree
        self.menu = Menu(root, tearoff=0)
        self.menu.add_command(label="Save", command=self.save)
 
    def get_selection(self):
        ''' Return selection pruning duplicates '''
        self.root.config(cursor="wait")
        self.root.update()
        nodes = []
        last = None
        for node in self.tree.selection():
            if last != node.split(':')[0]:
                nodes.append(node)
                last = node
        return nodes

    def save(self):
        ''' Group a device '''
        for node in self.get_selection():
            index = node.split()
            temp = len(index)
            if temp == 1:
                DFS.write_ssd(int(index[0]))
            elif temp == 2:
                DFS.write_file(int(index[0]), int(index[1]))
        self.root.config(cursor="")

def menu(root):
    ''' Menu Bar '''
    menu = Menu(root)
    root.config(menu=menu)
    filemenu = Menu(menu)
    menu.add_cascade(label="File", menu=filemenu)
    filemenu.add_command(label="Open", command=Open)
    #filemenu.add_command(label="Close", command=Close)
    filemenu.add_separator()
    filemenu.add_command(label="New SSD", command=NewSSD)
    filemenu.add_command(label="New MMB", command=NewMMB)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=root.quit)

    helpmenu = Menu(menu)
    menu.add_cascade(label="Help", menu=helpmenu)
    helpmenu.add_command(label="About...", command=About)
    # menu(root)

def tree(root):
    ''' Build a Tree '''
    def do_popup(event):
        ''' Bring up Pop Up menu '''
        if tree.focus() is not None:
            popup.menu.post(event.x_root, event.y_root)

    def add_disks():
        ''' Add a device to the tree '''
        for disk_index, disk in enumerate(DFS.disk_info):
            if disk:
                detail = f"Contains {disk['file_count']} file(s)"
                dev = tree.insert("", "end", [disk_index], text=disk['title'], values=detail)
                for file_index, info in enumerate(disk['file_info']):
                    columns = (f"{info['load_&']:08X}", f"{info['exec_&']:08X}", f"{info['size']:06X}")
                    tree.insert(dev, "end", [disk_index, file_index], text=info['name'], values=columns)

    tree = Treeview(root)
    tree["columns"] = ('Start', 'Execute', 'Length', 'Sector')
    tree.column("#0", width=350)
    tree.column("Execute", width=100)
    tree.column("Length", width=70)
    tree.column("Sector", width=120)
    tree.heading("Start", text="Start &")
    tree.heading("Execute", text="Execute &")
    tree.heading("Length", text="Length")
    add_disks()
    popup = Popup(root, tree)
    tree.bind("<Button-3>", do_popup)
    tree.pack(fill=Y, side=LEFT)


def gui():
    root = Tk()
    root.title("Acorn DFS")
    root.geometry("1024x768")
    # root.iconbitmap(bitmap=os.path.join(os.path.dirname(__file__), 'Owl.ico'))
    #dfs = acorn_dfs("ROMs1.ssd")

    menu(root)
    tree(root)

    # icons = get_icons()
    # for index, info in enumerate(devices):
    #    add_device(index, info)
    root.mainloop()


# read_disk(get_file())
# read_mmb(get_file('mmb'))
DFS = acorn_dfs("BEEB.mmb")
gui()
