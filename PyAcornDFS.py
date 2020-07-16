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


def read_catalogue(data):
    ''' Read the catalogue from the disk '''
    disk_info = read_disk_info(data)
    if disk_info:
        file_info = []
        for index in range(1, disk_info['file_count'] + 1):
            file_info.insert(index, read_file_info(data, index * 8))
        disk_info['file_info'] = file_info
        # print(disk_info)
    return disk_info


def show_catalogue(disk_info):
    ''' Show the catalogue of and SSD '''
    print(f"{disk_info['title']} Contains {disk_info['file_count']} file(s)")
    for info in disk_info['file_info']:
        print(
            f"    {info['ext']}.{info['name']} {info['lock']} {info['load_&']:08X} {info['exec_&']:08X} {info['size']:06X} {info['start']:03X}"
        )


def read_ssd(filename, offset=0):
    ''' Read in a DFS Disk '''
    with open(filename, "rb") as file_p:
        data = file_p.read(DISK_SIZE)
        return read_catalogue(data)
    return None


def get_disk_count(filename):
    ''' Calculate the number of disks in an MMB '''
    size = os.path.getsize(filename)
    if size >= MMB_HEADER:
        size -= MMB_HEADER
        disk_count = size // DISK_SIZE
        if disk_count and (disk_count <= 511):
            print(f"MMB Has {disk_count} Disks")
            return disk_count
    return None


def read_mmb(filename):
    ''' Read an MMB file '''
    disk_count = get_disk_count(filename)
    if disk_count:
        with open(filename, "rb") as file_p:
            for disk in range(disk_count):
                file_p.seek(MMB_HEADER + (DISK_SIZE * disk))
                data = file_p.read(DISK_SIZE)  # Was 0x200 now read the whole SSD in!
                disk_info = read_catalogue(data)
                if disk_info:
                    show_catalogue(disk_info)
                    # write_ssd(disk, data, disk_info)


if __name__ == "__main__":
    # make_disks(20)
    # pad_disk("ROMs1.ssd")
    # pad_disk("WatfordROMram.ssd")
    read_mmb('BEEB.mmb')
    # disk_info, file_info = read_disk("ROMs1.ssd")
    # show_catalogue(disk_info, file_info)
