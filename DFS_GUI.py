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


def OpenMMB():
    name = askopenfilename()
    print(name)


def NewMMB():
    print("New File!")


def OpenSSD():
    name = askopenfilename()
    print(name)


def NewSSD():
    print("New File!")


def About():
    open_new("https://github.com/fordp2002/PyAcornDFS")


def menu(root):
    ''' Menu Bar '''
    menu = Menu(root)
    root.config(menu=menu)
    filemenu = Menu(menu)
    menu.add_cascade(label="File", menu=filemenu)
    filemenu.add_command(label="Open MMB", command=OpenMMB)
    filemenu.add_command(label="New MMB", command=NewMMB)
    filemenu.add_separator()
    filemenu.add_command(label="Open SSD", command=OpenSSD)
    filemenu.add_command(label="New SSD", command=NewSSD)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=root.quit)

    helpmenu = Menu(menu)
    menu.add_cascade(label="Help", menu=helpmenu)
    helpmenu.add_command(label="About...", command=About)
    # menu(root)


def tree(root):
    ''' Build a Tree '''

    def add_ssd(filename):
        ''' Add a device to the tree '''
        disk = acorn_dfs(filename).disk_info[0]
        if disk:
            detail = f"Contains {disk['file_count']} file(s)"
            dev = tree.insert("", "end", disk['title'], text=disk['title'], values=detail)
            for index, info in enumerate(disk['file_info']):
                columns = (f"{info['load_&']:08X}", f"{info['exec_&']:08X}", f"{info['size']:06X}")
                ref = f'File:{index}'
                tree.insert(dev, "end", ref, text=info['name'], values=columns)

    tree = Treeview(root)
    tree["columns"] = ('Start', 'Execute', 'Length', 'Sector')
    tree.column("#0", width=350)
    tree.column("Execute", width=100)
    tree.column("Length", width=70)
    tree.column("Sector", width=120)
    tree.heading("Start", text="Start &")
    tree.heading("Execute", text="Execute &")
    tree.heading("Length", text="Length")
    add_ssd("ROMs1.ssd")
    tree.pack(fill=Y, side=LEFT)


def gui():
    root = Tk()
    root.title("Acorn DFS")
    root.geometry("1024x768")
    # root.iconbitmap(bitmap=os.path.join(os.path.dirname(__file__), 'Owl.ico'))
    menu(root)
    tree(root)
    # popup = Popup(root, tree)
    # tree.bind("<Button-3>", do_popup)

    # icons = get_icons()
    # for index, info in enumerate(devices):
    #    add_device(index, info)
    root.mainloop()


# read_disk(get_file())
# read_mmb(get_file('mmb'))
gui()
