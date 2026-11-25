# PyAcornDFS

This project is intended to support manipulating Acorn DFS .ssd, .dsd and .mmb files on a modern computer using Python 3.
It is an open source hobby project not at all ready for production use at the time of writing!

The program is split into a library and two GUIs, in the `src/pyacorndfs` package:

| Module | Purpose |
| --- | --- |
| `dfs.py` | The DFS image library (`acorn_dfs`) |
| `gui.py` | The Tkinter GUI |
| `wx_gui.py` | The wxPython GUI (native widgets) |
| `basic.py` | BBC BASIC detokeniser |
| `disasm.py` | Adapter to the [py8dis](https://github.com/ZornsLemma/py8dis) disassembler |

## How PyAcornDFS and py8dis fit together

PyAcornDFS is the application: it owns everything Acorn-specific (disc images, the GUIs, the "Disassemble" action). [py8dis](https://github.com/ZornsLemma/py8dis) is an independent, unmodified project used as a library:

- It is a git submodule in `external/py8dis`, pinned to a specific upstream commit. PyAcornDFS contains no copy of py8dis code and py8dis contains no DFS code, so each can be updated independently.
- `src/pyacorndfs/disasm.py` is the only module that knows py8dis exists. The GUIs call `acorn_dfs.disassemble()`, which calls `disasm.disassemble()`.
- For each file, `disasm.py` writes the raw file and a py8dis control script (`load()`, `acorn.bbc()`, `entry()`, `go()`) built from the DFS catalogue, then runs that script with `python3` in a **separate process** with `PYTHONPATH` pointing at `external/py8dis/py8dis`. py8dis keeps its state in module globals and reads the command line on import, so a fresh process per run keeps runs independent and stops a py8dis failure taking down the GUI.
- The listing py8dis prints is saved as `NAME.6502` (BeebASM). The control script is kept as `NAME.py` so it can be refined by hand, the normal py8dis workflow.
- py8dis is located via the `PY8DIS_PATH` environment variable if set (the directory holding `commands.py`), otherwise the submodule. If neither is present, "Disassemble" is greyed out and everything else still works.

Previously the DFS code lived inside a fork of py8dis; that fork's `master` is now plain upstream and the old combined code is kept on its `dfs-experiment` branch for reference only.

## Setting up on a new machine (Ubuntu)

1. System packages - Python 3.10 or later with Tk, and git:

   ```sh
   sudo apt install git python3 python3-tk python3-venv
   ```

2. Clone, including the py8dis submodule:

   ```sh
   git clone --recurse-submodules https://github.com/fordp2002/PyAcornDFS
   cd PyAcornDFS
   ```

   If you cloned without `--recurse-submodules`, run `git submodule update --init`.

3. Python packages - `tkinterdnd2` (drag and drop) and `wxPython` (wx GUI); py8dis itself needs nothing extra. Either into the system Python, or into a project-local virtual environment:

   ```sh
   python3 -m venv .venv
   . .venv/bin/activate
   python -m pip install -r requirements.txt -r requirements-dev.txt
   ```

   pip may build wxPython from source, which is slow; `sudo apt install python3-wxgtk4.0` is a quicker alternative for the system Python.

4. Check it works: `python3 -m pytest` should pass, including the disassembly tests (they are skipped if the submodule is missing).

5. Optional desktop menu entry - create `~/.local/share/applications/PyAcornDFS.desktop`, using the interpreter from step 3 and your clone's path:

   ```ini
   [Desktop Entry]
   Type=Application
   Name=PyAcornDFS
   Comment=Open SSD DSD and MMB Files
   Exec=/usr/bin/python3 /path/to/PyAcornDFS/DFS_GUI.py %f
   Path=/path/to/PyAcornDFS/
   Icon=/path/to/PyAcornDFS/src/pyacorndfs/dfs_floppy.png
   Terminal=false
   Categories=Utility;X-Retro;
   ```

   `%f` passes the image when opened from Dolphin's "Open with". Use `DFS_WX_GUI.py` for the wx GUI.

### Existing clones

The submodule used to point at the fordp2002 fork and now points at upstream. In a clone made before that change, run once:

```sh
git pull
git submodule sync
git submodule update --init
```

### Updating py8dis

To move to a newer upstream py8dis, then re-run the tests and commit the new pin:

```sh
git -C external/py8dis pull origin master
python3 -m pytest
git add external/py8dis && git commit -m "Update py8dis"
```

## Running

From a source checkout:

```sh
python3 DFS_GUI.py                    # Tkinter GUI
python3 DFS_WX_GUI.py                 # wxPython GUI
python3 DFS_WX_GUI.py /path/to/disk.ssd
```

Passing an image path opens it at startup, which is what Dolphin's "Open with" menu does. Alternatively `pip install -e .` and run `pyacorndfs` (Tkinter), `pyacorndfs --wx`, or `python -m pyacorndfs [--wx] [IMAGE]`.

## Using it

Open a file (SSD, DSD or MMB) from the "File -> Open" menu, or drop one on the window, and it loads into the tree. Then select node(s) and right click:

- **Save** writes a disk as an SSD, or a file to the host, into the same directory as the image.
- **Save DSD** writes a disk and the one after it as an interleaved DSD; if there is no next side, the second side is blank.
- **Extract BASIC** writes a detokenised `NAME.bas`.
- **Mode Zero** shows the file as a Mode 0 screen.
- **Disassemble** runs py8dis on a file and writes, next to the image:
  - `NAME` - the raw file
  - `NAME.py` - the py8dis control script, ready to refine by hand and re-run
  - `NAME.6502` - the BeebASM listing

In the wx GUI, select two SSD images in the Open dialog to load them together as a double-sided image.

### Disassembly notes

- The 6502 address is the low 16 bits of the DFS load/exec address. I/O processor addresses (`&FFxxxx`) and other high bits are recorded in a comment at the top of the listing.
- Tracing starts at the exec address when it lies inside the file, otherwise at the load address.
- A file that would run past `&FFFF` is truncated at the top of memory; the truncated copy is written as `NAME.trunc` so a full `NAME` is not overwritten.
- py8dis runs in a separate process, so a failure in it is reported in a message box and does not affect the GUI. To use a different py8dis checkout, set `PY8DIS_PATH` to its `py8dis` directory (the one holding `commands.py`).

To re-run an edited control script:

```sh
PYTHONPATH=external/py8dis/py8dis python3 NAME.py > NAME.6502
```

## Tests

```sh
python3 -m pytest
```
