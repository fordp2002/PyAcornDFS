''' Acorn DFS, library and GUI by Simon R. Ellwood '''
import os
import hashlib
from struct import pack_into, unpack_from
from BBCBasicToText import Decode

MMB_HEADER = 0x2000
DISK_SIZE = 256 * 10 * 80  # Sector size, Sector Count, Track Count


def from_acorn(text):
    ''' Convert from cp1252 to Acorn ASCII '''
    if text[0]:
        return str(text, 'cp1252').rstrip('\x00').rstrip().replace('`', '£')
    return ""


def make_blank_ssd(filename):
    ''' Create a 200K Image '''
    data = bytearray(b'\x00') * DISK_SIZE
    pack_into('H', data, 0x106, 800)  # 80 Sectors with 10 Sectors Per Track
    with open(filename, "wb") as file_p:
        file_p.write(data)


def make_disks(count):
    ''' Make DFS Disks '''
    for index in range(count):
        make_blank_ssd(f"DSKA{index:04d}.ssd")


def pad_disk(filename):
    ''' Pad an SSD '''
    used = os.path.getsize(filename)
    if used < DISK_SIZE:
        pad = DISK_SIZE - used
        print(f"{filename} is {used} 0x{used:04X} PAD = {pad:04X}")
        data = bytearray(b'\xFF') * pad
        with open(filename, "ab+") as file_p:
            file_p.write(data)


def extra_bits(value, bits, address=False):
    ''' Return 2 bits from a byte '''
    temp = (value >> bits) & 3
    if address and (temp == 3):
        return 0xFFFF
    return temp


def read_disk_info(data, offset=0):
    ''' Read the Disc descriptor '''
    info = {}
    title1 = unpack_from('8s', data, offset)[0]
    title2, info['cycle'], file_count, extra, sector_count = unpack_from(
        '4sBBBB', data, offset + 256
    )
    info['title'] = from_acorn(title1 + title2)
    info['file_count'] = file_count >> 3
    info['boot'] = extra_bits(extra, 4)
    sector_count += extra_bits(extra, 0) << 8
    if sector_count != 400 and sector_count != 800:
        return None
    info['sector_count'] = sector_count
    return info


def read_file_info(data, offset):
    ''' Read the information about a single file '''
    info = {}
    name, ext = unpack_from('7sB', data, offset)
    try:
        info['name'] = from_acorn(name)
    except:
        info['name'] = "Illegal"
    info['lock'] = 'L' if ext & 0x80 else ' '
    info['ext'] = chr(ext & 0x7F)
    info['load_&'], info['exec_&'], info['size'], extra, info['start'] = unpack_from(
        'HHHBB', data, offset + 256
    )
    info['start'] += extra_bits(extra, 0) << 8
    info['load_&'] += extra_bits(extra, 2, True) << 16
    info['size'] += extra_bits(extra, 4) << 16
    info['exec_&'] += extra_bits(extra, 6, True) << 16

    info['offset'] = offset + (info['start'] << 8)
    return info


def read_surface(file_p, offset, size):
    ''' Read part or all of a disk '''
    file_p.seek(offset)
    return file_p.read(size)


def read_catalogue(file_p, offset=0):
    ''' Read the catalogue from the disk '''
    data = read_surface(file_p, offset, 0x200)
    disk_info = read_disk_info(data)
    if disk_info:
        disk_info["offset"] = offset
        file_info = []
        for index in range(1, disk_info['file_count'] + 1):
            file_info.insert(index, read_file_info(data, index * 8))
        disk_info['file_info'] = file_info
    return disk_info


def read_disks(filename, disk_count, offset=0):
    ''' Read an MMB file '''
    disk_info = []
    if disk_count:
        with open(filename, "rb") as file_p:
            for _ in range(disk_count):
                disk_info.append(read_catalogue(file_p, offset))
                offset += DISK_SIZE
    return disk_info


def read_ssd(filename):
    ''' Read in a SSD Image '''
    disk_count = 1 if os.path.getsize(filename) < (DISK_SIZE + 0x200) else 2
    return read_disks(filename, disk_count)


def get_disk_count(filename):
    ''' Calculate the number of disks in an MMB '''
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
    ''' Read an MMB file '''
    return read_disks(filename, get_disk_count(filename), MMB_HEADER)

def convert_dsd(filename):
    ''' Convert an DSD Iamge to a Double Sided SSD Image '''
    if os.path.getsize(filename) == 0x64000:
        with open(filename, "rb") as file_p:
            data = file_p.read()
            side0 = bytes()
            side1 = bytes()
            offset = 0
            for _ in range(80):
                side0 += data[offset:offset + 0xA00]
                offset += 0xA00
                side1 += data[offset:offset + 0xA00]
                offset += 0xA00
        new_name = filename.replace('.dsd', '.ssd')
        with open(new_name, "wb") as file_p:
            file_p.write(side0 + side1)
        return new_name
    else:
        raise "Wrong Size"
    return None


class acorn_dfs:
    ''' Wrap the DFS Methods in a class '''

    def __init__(self, filename=None):
        ''' Open an parse the directories of a DFS File '''
        self.open_image(filename)

    def open_image(self, filename=None):
        ''' release a file (It is not open at this point)'''
        self.disk_info = None
        if filename:
            extension = os.path.splitext(filename)[1].lower()
            if extension == '.ssd':
                self.disk_info = read_ssd(filename)
            elif extension == '.dsd':
                filename = convert_dsd(filename)
                self.disk_info = read_ssd(filename)
            elif extension == '.mmb':
                self.disk_info = read_mmb(filename)
        self.filename = filename
        return filename

    def get_default_name(self, base_name):
        ''' Join the source directory to the filename '''
        dir_name = os.path.dirname(self.filename)
        return os.path.join(dir_name, base_name)

    def get_disk_title(self, index=0):
        ''' Get the title of one of the disks '''
        return self.disk_info[index]['title']

    def write_ssd(self, index, filename=None):
        ''' Write SSD from an MMB '''
        if index < len(self.disk_info):
            disk = self.disk_info[index]
            if filename is None:
                filename = self.get_default_name(f"DIN_{index}_{disk['title']}.ssd")
            with open(self.filename, "rb") as file_p:
                data = read_surface(file_p, disk['offset'], DISK_SIZE)
                with open(filename, 'wb') as file_p:
                    file_p.write(data)

    def get_data(self, disk_index, file_index):
        ''' Write a file from an SSD to disk '''
        disk = self.disk_info[disk_index]
        info = disk['file_info'][file_index]
        offset = disk["offset"] + (info["start"] * 256)
        size = info["size"]
        with open(self.filename, "rb") as read_p:
            data = read_surface(read_p, offset, size)
            return data, info['name']
        return None, None

    def write_file(self, disk_index, file_index, filename=None):
        ''' Write a file from an SSD to disk '''
        data, name = self.get_data(disk_index, file_index)
        if data:
            if filename == None:
                filename = self.get_default_name(name)
            with open(filename, "wb") as write_p:
                write_p.write(data)

    def extract_basic(self, disk_index, file_index, filename=None):
        ''' Write a file from an SSD to disk '''
        data, name = self.get_data(disk_index, file_index)
        if data:
            if filename == None:
                filename = self.get_default_name(f"{name}.bas")
            with open(filename, 'wb') as write_p:
                Decode(data, write_p)

    def get_md5(self, disk_index, file_index):
        ''' Get the MD5 Sum '''
        data, _filename = self.get_data(disk_index, file_index)
        return hashlib.md5(data).hexdigest().upper()

    def show_catalogue(self, show_blank=False):
        ''' Show the catalogue(s) of file '''
        for index, disk in enumerate(self.disk_info):
            if disk:
                print(f"{disk['title']} Contains {disk['file_count']} file(s)")
                for num, info in enumerate(disk['file_info']):
                    print(f'{num} {self.get_md5(index, num)}')
                    print(
                        f"    {info['ext']}.{info['name']} {info['lock']} {info['load_&']:08X} {info['exec_&']:08X} {info['size']:06X} {info['start']:03X}"
                    )

            elif show_blank:
                print(f"DIN {index} is blank")


if __name__ == "__main__":
    # make_disks(20)
    # pad_disk("ROMs1.ssd")
    # pad_disk("WatfordROMram.ssd")
    # acorn_dfs('BEEB.mmb').show_catalogue()
    # acorn_dfs("ROMs1.ssd").show_catalogue()
    acorn_dfs("PCBCAD.ssd").show_catalogue()
