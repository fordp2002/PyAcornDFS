''' Acorn DFS, library and GUI by Simon R. Ellwood '''
import os
from struct import pack_into, unpack_from

MMB_HEADER = 0x2000
DISK_SIZE = 256 * 10 * 80  # Sector size, Sector Count, Track Count


def make_blank_disk(filename):
    ''' Create a 200K Image '''
    data = bytearray(b'\x00') * DISK_SIZE
    pack_into('H', data, 0x106, 800)  # 80 Sectors with 10 Sectors Per Track
    with open(filename, "wb") as file_p:
        file_p.write(data)


def make_disks(count):
    ''' Make DFS Disks '''
    for index in range(count):
        make_blank_disk(f"DSKA{index:04d}.ssd")


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
    info['title'] = str(title1 + title2, 'utf8').rstrip('\x00').rstrip() if title1[0] else ""
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
        info['name'] = str(name, 'utf8')
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


def write_ssd(disk, data, disk_info):
    ''' Write SSD from an MMB '''
    filename = f"DIN_{disk}_{disk_info['title']}.ssd"
    with open(filename, 'wb') as file_p:
        file_p.write(data)


def read_catalogue(file_p, offset=0):
    ''' Read the catalogue from the disk '''
    file_p.seek(offset)
    data = file_p.read(0x200)
    disk_info = read_disk_info(data)
    if disk_info:
        disk_info[offset] = offset
        file_info = []
        for index in range(1, disk_info['file_count'] + 1):
            file_info.insert(index, read_file_info(data, index * 8))
        disk_info['file_info'] = file_info
    return disk_info


def get_disk_count(filename):
    ''' Calculate the number of disks in an MMB '''
    size = os.path.getsize(filename)
    if size >= MMB_HEADER:
        size -= MMB_HEADER
        disk_count = size // DISK_SIZE
        if disk_count and (disk_count <= 511):
            return disk_count
    return None


def read_mmb(filename):
    ''' Read an MMB file '''
    disk_info = []
    disk_count = get_disk_count(filename)
    if disk_count:
        with open(filename, "rb") as file_p:
            for index in range(disk_count):
                offset = MMB_HEADER + (DISK_SIZE * index)
                disk_info.append(read_catalogue(file_p, offset))
    return disk_info


def read_ssd(filename):
    ''' Read in a DFS Disk '''
    with open(filename, "rb") as file_p:
        return [read_catalogue(file_p)]
    return None

class acorn_dfs:
    ''' Wrap the DFS Methods in a class '''

    def __init__(self, filename):
        ''' Open an parse the directories of a DFS File '''
        self.filename = filename
        self.disk_info = None
        if self.filename:
            extension = os.path.splitext(self.filename)[1].lower()
            if extension == '.ssd':
                self.disk_info = read_ssd(self.filename)
                return
            if extension == '.mmb':
                self.disk_info = read_mmb(self.filename)

    def write_ssd(self, index):
        ''' Write SSD from an MMB '''
        if index < len(self.disk_info):
            disk = self.disk_info[index]
        with open(self.filename, "rb") as file_p:
            file_p.seek(disk['offset'])
            data = file_p.read(DISK_SIZE)            
            filename = f"DIN_{index}_{disk['title']}.ssd"
            with open(filename, 'wb') as file_p:
                file_p.write(data)

    def show_catalogue(self, show_blank=False):
        ''' Show the catalogue(s) of file '''
        for index, disk in enumerate(self.disk_info):
            if disk:
                print(f"{disk['title']} Contains {disk['file_count']} file(s)")
                for info in disk['file_info']:
                    print(
                        f"    {info['ext']}.{info['name']} {info['lock']} {info['load_&']:08X} {info['exec_&']:08X} {info['size']:06X} {info['start']:03X}"
                    )
            elif show_blank:
                print(f"DIN {index} is blank")


if __name__ == "__main__":
    # make_disks(20)
    # pad_disk("ROMs1.ssd")
    # pad_disk("WatfordROMram.ssd")
    acorn_dfs('BEEB.mmb').show_catalogue()
    # acorn_dfs("ROMs1.ssd").show_catalogue()
