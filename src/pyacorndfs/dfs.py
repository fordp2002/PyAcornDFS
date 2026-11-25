"""Acorn DFS, library and GUI by Simon R. Ellwood"""

import os
import hashlib
import io
from os import path
from struct import pack_into, unpack_from
from .basic import Decode

MMB_HEADER = 0x2000
DISK_SIZE = 256 * 10 * 80  # Sector size, Sector Count, Track Count
TRACK_SIZE = 0xA00
TRACK_COUNT = 80


def from_acorn(text):
    """Convert from cp1252 to Acorn ASCII"""
    if text[0]:
        return str(text, "cp1252").rstrip("\x00").rstrip().replace("`", "£")
    return ""


def make_blank_ssd(filename, size=DISK_SIZE):
    """Create a 200K Image"""
    data = _make_blank_ssd_data(size)
    with open(filename, "wb") as file_p:
        file_p.write(data)


def _make_blank_ssd_data(size):
    data = bytearray(size)
    sector_count = size >> 8
    pack_into("BB", data, 0x106, sector_count >> 8, sector_count & 0xFF)
    return data


def make_disks(count):
    """Make DFS Disks"""
    for index in range(count):
        make_blank_ssd(f"DSKA{index:04d}.ssd")


def pad_disk(filename):
    """Pad an SSD"""
    used = os.path.getsize(filename)
    if used < DISK_SIZE:
        pad = DISK_SIZE - used
        print(f"{filename} is {used} 0x{used:04X} PAD = {pad:04X}")
        data = bytearray(b"\xff") * pad
        with open(filename, "ab+") as file_p:
            file_p.write(data)


def extra_bits(value, bits, address=False):
    """Return 2 bits from a byte"""
    temp = (value >> bits) & 3
    if address and (temp == 3):
        return 0xFFFF
    return temp


def read_disk_info(data, offset=0):
    """Read the Disc descriptor"""
    info = {}
    title1 = unpack_from("8s", data, offset)[0]
    title2, info["cycle"], file_count, extra, sector_count = unpack_from(
        "4sBBBB", data, offset + 256
    )
    info["title"] = from_acorn(title1 + title2)
    info["file_count"] = file_count >> 3
    info["boot"] = extra_bits(extra, 4)
    sector_count += extra_bits(extra, 0) << 8
    # if sector_count != 400 and sector_count != 800:
    #    return None
    info["sector_count"] = sector_count
    return info


def read_file_info(data, offset):
    """Read the information about a single file"""
    info = {}
    name, ext = unpack_from("7sB", data, offset)
    try:
        info["name"] = from_acorn(name)
    except:
        info["name"] = "Illegal"
    info["lock"] = "L" if ext & 0x80 else " "
    info["ext"] = chr(ext & 0x7F)
    info["load_&"], info["exec_&"], info["size"], extra, info["start"] = unpack_from(
        "HHHBB", data, offset + 256
    )
    info["start"] += extra_bits(extra, 0) << 8
    info["load_&"] += extra_bits(extra, 2, True) << 16
    info["size"] += extra_bits(extra, 4) << 16
    info["exec_&"] += extra_bits(extra, 6, True) << 16

    info["offset"] = offset + (info["start"] << 8)
    return info


def read_surface(file_p, offset, size):
    """Read part or all of a disk"""
    file_p.seek(offset)
    return file_p.read(size)


def read_catalogue(file_p, offset=0):
    """Read the catalogue from the disk"""
    data = read_surface(file_p, offset, 0x200)
    disk_info = read_disk_info(data)
    if disk_info:
        disk_info["offset"] = offset
        file_info = []
        for index in range(1, disk_info["file_count"] + 1):
            file_info.insert(index, read_file_info(data, index * 8))
        disk_info["file_info"] = file_info
    return disk_info


def read_disks(filename, disk_count, offset=0):
    """Read an MMB file"""
    disk_info = []
    if disk_count:
        with open(filename, "rb") as file_p:
            for _ in range(disk_count):
                disk_info.append(read_catalogue(file_p, offset))
                offset += DISK_SIZE
    return disk_info


def read_ssd(filename):
    """Read in a SSD Image"""
    disk_count = 1 if os.path.getsize(filename) < (DISK_SIZE + 0x200) else 2
    return read_disks(filename, disk_count)


def get_disk_count(filename):
    """Calculate the number of disks in an MMB"""
    size = os.path.getsize(filename)
    if size >= MMB_HEADER:
        size -= MMB_HEADER
        disk_count, rem = divmod(size, DISK_SIZE)
        if rem:
            print("MMB is oversize by {rem} bytes")
        if disk_count and (disk_count <= 511):
            return disk_count
    return None


def read_mmb(filename):
    """Read an MMB file"""
    return read_disks(filename, get_disk_count(filename), MMB_HEADER)


def deinterleave_dsd(data):
    """Return a DSD image with each side stored contiguously."""
    if len(data) != DISK_SIZE * 2:
        raise ValueError(f"DSD image must be {DISK_SIZE * 2} bytes")

    sides = [bytearray(DISK_SIZE), bytearray(DISK_SIZE)]
    for track in range(TRACK_COUNT):
        source_offset = track * TRACK_SIZE * 2
        side_offset = track * TRACK_SIZE
        for side in range(2):
            start = source_offset + side * TRACK_SIZE
            sides[side][side_offset : side_offset + TRACK_SIZE] = data[
                start : start + TRACK_SIZE
            ]
    return bytes(sides[0] + sides[1])


def interleave_dsd(data):
    """Return two contiguous sides in DSD track-interleaved order."""
    if len(data) != DISK_SIZE * 2:
        raise ValueError(f"DSD image must be {DISK_SIZE * 2} bytes")

    interleaved = bytearray(DISK_SIZE * 2)
    for track in range(TRACK_COUNT):
        side_offset = track * TRACK_SIZE
        dsd_offset = track * TRACK_SIZE * 2
        for side in range(2):
            start = side * DISK_SIZE + side_offset
            destination = dsd_offset + side * TRACK_SIZE
            interleaved[destination : destination + TRACK_SIZE] = data[
                start : start + TRACK_SIZE
            ]
    return bytes(interleaved)


def convert_dsd(filename):
    """Convert a DSD image to a double-sided SSD image."""
    with open(filename, "rb") as file_p:
        data = deinterleave_dsd(file_p.read())
    new_name = os.path.splitext(filename)[0] + ".ssd"
    with open(new_name, "wb") as file_p:
        file_p.write(data)
    return new_name


def get_acorn_filename(filename):
    """Get the Acorn Filename from a modern filename"""
    if path.isfile(filename):
        base, ext = os.path.splitext(os.path.basename(filename))
        return base[:7], ext[1]
    return None


class acorn_dfs:
    """Wrap the DFS Methods in a class"""

    def __init__(self, filename=None):
        """Open an parse the directories of a DFS File"""
        self.open_image(filename)

    def open_image(self, filename=None):
        """release a file (It is not open at this point)"""
        self.disk_info = None
        self._normalized_dsd = None
        self.source_filenames = (filename,) if filename else ()
        if filename:
            extension = os.path.splitext(filename)[1].lower()
            if extension == ".ssd":
                self.disk_info = read_ssd(filename)
            elif extension == ".dsd":
                with open(filename, "rb") as file_p:
                    self._normalized_dsd = deinterleave_dsd(file_p.read())
                data = io.BytesIO(self._normalized_dsd)
                self.disk_info = [
                    read_catalogue(data, offset) for offset in (0, DISK_SIZE)
                ]
            elif extension == ".mmb":
                self.disk_info = read_mmb(filename)
        self.filename = filename
        return filename

    def open_ssd_pair(self, side0_filename, side1_filename):
        """Open two single-sided images as the sides of one DSD."""
        disk_info = []
        sides = []
        filenames = (side0_filename, side1_filename)
        for side_index, filename in enumerate(filenames):
            if os.path.splitext(filename)[1].lower() != ".ssd":
                raise ValueError("Both files must be SSD images")
            size = os.path.getsize(filename)
            if not DISK_SIZE <= size < DISK_SIZE + 0x200:
                raise ValueError("Each SSD must contain exactly one disk surface")

            with open(filename, "rb") as file_p:
                sides.append(read_surface(file_p, 0, DISK_SIZE))
                disk = read_catalogue(file_p)
            disk["offset"] = side_index * DISK_SIZE
            disk_info.append(disk)

        self.disk_info = disk_info
        self._normalized_dsd = b"".join(sides)
        self.filename = side0_filename
        self.source_filenames = filenames
        return self.filename

    def _read_image_surface(self, offset, size):
        """Read a logical image range, accounting for DSD track interleaving."""
        if self._normalized_dsd is not None:
            return self._normalized_dsd[offset : offset + size]
        with open(self.filename, "rb") as file_p:
            return read_surface(file_p, offset, size)

    def get_default_name(self, base_name, ext=None):
        """Join the source directory to the filename"""
        if ext and ext != "$":
            base_name += "." + ext
        dir_name = os.path.dirname(self.filename)
        return os.path.join(dir_name, base_name)

    def get_disk_title(self, index=0):
        """Get the title of one of the disks"""
        return self.disk_info[index]["title"]

    def write_ssd(self, index, filename=None):
        """Write SSD from an MMB"""
        if index < len(self.disk_info):
            disk = self.disk_info[index]
            if filename is None:
                filename = self.get_default_name(f"DIN_{index}_{disk['title']}", "ssd")
            data = self._read_image_surface(disk["offset"], DISK_SIZE)
            with open(filename, "wb") as file_p:
                file_p.write(data)

    def write_dsd(self, index, filename=None):
        """Write two consecutive surfaces as a DSD, blank-padding the last."""
        if not 0 <= index < len(self.disk_info):
            raise IndexError("DSD start surface is out of range")

        disk = self.disk_info[index]
        first_side = self._read_image_surface(disk["offset"], DISK_SIZE)
        if index + 1 < len(self.disk_info):
            next_disk = self.disk_info[index + 1]
            second_side = self._read_image_surface(next_disk["offset"], DISK_SIZE)
        else:
            second_side = _make_blank_ssd_data(DISK_SIZE)

        if filename is None:
            filename = self.get_default_name(f"DIN_{index}_{disk['title']}", "dsd")
        with open(filename, "wb") as file_p:
            file_p.write(interleave_dsd(first_side + second_side))

    def get_data(self, disk_index, file_index):
        """Write a file from an SSD to disk"""
        disk = self.disk_info[disk_index]
        info = disk["file_info"][file_index]
        offset = disk["offset"] + (info["start"] * 256)
        size = info["size"]
        data = self._read_image_surface(offset, size)
        return data, info["name"], info["ext"]

    def write_file(self, disk_index, file_index, filename=None):
        """Write a file from an SSD to disk"""
        data, name, ext = self.get_data(disk_index, file_index)
        if data:
            if filename == None:
                filename = self.get_default_name(name, ext)
            with open(filename, "wb") as write_p:
                write_p.write(data)

    def extract_basic(self, disk_index, file_index, filename=None):
        """Extract Basic Text from an SSD to disk"""
        data, name, _ext = self.get_data(disk_index, file_index)
        if data:
            if filename == None:
                filename = self.get_default_name(name, "bas")
            with open(filename, "wb") as write_p:
                Decode(data, write_p)

    def disassemble(self, disk_index, file_index, out_dir=None):
        """Disassemble Machine Code from a file with py8dis.

        Writes NAME, NAME.py (py8dis control script) and NAME.6502 (BeebASM)
        next to the image unless out_dir is given. Returns a DisasmResult.
        """
        from . import disasm

        data, name, ext = self.get_data(disk_index, file_index)
        if not data:
            return None
        info = self.disk_info[disk_index]["file_info"][file_index]
        if out_dir is None:
            out_dir = os.path.dirname(self.filename) or os.getcwd()
        base_name = name if ext == "$" else f"{name}.{ext}"
        return disasm.disassemble(data, info["load_&"], info["exec_&"], base_name, out_dir)

    def get_md5(self, disk_index, file_index):
        """Get the MD5 Sum"""
        data = self.get_data(disk_index, file_index)[0]
        return hashlib.md5(data).hexdigest().upper()

    def show_catalogue(self, show_blank=False):
        """Show the catalogue(s) of file"""
        for index, disk in enumerate(self.disk_info):
            if disk:
                print(f"{disk['title']} Contains {disk['file_count']} file(s)")
                for num, info in enumerate(disk["file_info"]):
                    print(f"{num} {self.get_md5(index, num)}")
                    print(
                        f"    {info['ext']}.{info['name']} {info['lock']} {info['load_&']:08X} {info['exec_&']:08X} {info['size']:06X} {info['start']:03X}"
                    )

            elif show_blank:
                print(f"DIN {index} is blank")

    def last_used_sector(self, disk_index):
        """Get the last used sector of a disk"""
        last = 2  # The first two sectors are used for the catalogue and directory
        disk = self.disk_info[disk_index]
        for info in disk["file_info"]:
            end = info["start"] + (info["size"] >> 8)
            if end > last:
                last = end
        return last

    def get_free_space_bytes(self, disk_index):
        """Get the free space on a disk"""
        last = self.last_used_sector(disk_index)
        disk = self.disk_info[disk_index]
        return (disk["sector_count"] - last) << 8

    def add_file(self, disk_index, filename):  # Not finsihed yet
        """Add a file to a disk"""
        disk = self.disk_info[disk_index]
        free_space = self.get_free_space_bytes(disk_index)
        size = os.path.getsize(filename)
        if size <= free_space:
            with open(filename, "rb") as file_p:
                data = file_p.read()
                offset = disk["offset"] + (self.last_used_sector(disk_index) << 8)
                with open(self.filename, "r+b") as write_p:
                    write_p.seek(offset)
                    write_p.write(data)
            return True
        return False


def test():
    # make_disks(20)
    # pad_disk("ROMs1.ssd")
    # pad_disk("WatfordROMram.ssd")
    # acorn_dfs('BEEB.mmb').show_catalogue()
    # acorn_dfs("ROMs1.ssd").show_catalogue()
    # acorn_dfs("PCBCAD.ssd").show_catalogue()
    filename = os.path.join(os.getcwd(), "jgh007.ssd")
    disks = acorn_dfs(filename)
    print(disks.last_used_sector(0))
    print(disks.get_free_space_bytes(0))


if __name__ == "__main__":
    print(get_acorn_filename("/home/simone/Documents/UMI4B/CHIMAI.MID"))
