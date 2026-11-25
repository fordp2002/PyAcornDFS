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
| `disasm.py` | Adapter to the [py8dis](https://github.com/fordp2002/py8dis) disassembler |

## Getting the code

py8dis is included as a git submodule in `external/py8dis`, so clone with:

```sh
git clone --recurse-submodules https://github.com/fordp2002/PyAcornDFS
```

or, in an existing clone, `git submodule update --init`. Without the submodule everything works except "Disassemble", which is greyed out.

## Running

The GUIs need `tkinterdnd2` (drag and drop) and, for the wx version, `wxPython`. On Ubuntu the system Python can be used directly once those are installed; otherwise use a project-local virtual environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

On Kubuntu, if creating the environment fails because `venv` is unavailable, install it with `sudo apt install python3-venv`.

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
