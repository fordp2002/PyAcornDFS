import os
import struct
import tempfile
import unittest

from pyacorndfs.dfs import DISK_SIZE, MMB_HEADER, acorn_dfs, deinterleave_dsd


TRACK_SIZE = 0xA00


def make_dsd_image():
    normalized = bytearray(DISK_SIZE * 2)
    for side, title in enumerate((b"SIDE 0  ", b"SIDE 1  ")):
        side_offset = side * DISK_SIZE
        normalized[side_offset : side_offset + 8] = title
        file_count = 8 if side == 1 else 0
        sector_count = 800
        struct.pack_into(
            "4sBBBB",
            normalized,
            side_offset + 256,
            b"    ",
            0,
            file_count,
            sector_count >> 8,
            sector_count & 0xFF,
        )

    side1_offset = DISK_SIZE
    struct.pack_into("7sB", normalized, side1_offset + 8, b"SECOND ", ord("$"))
    struct.pack_into(
        "HHHBB",
        normalized,
        side1_offset + 264,
        0,
        0,
        4,
        0,
        2,
    )
    normalized[side1_offset + 2 * 256 : side1_offset + 2 * 256 + 4] = b"DATA"

    interleaved = bytearray(DISK_SIZE * 2)
    for track in range(80):
        track_offset = track * TRACK_SIZE
        for side in range(2):
            source = side * DISK_SIZE + track_offset
            destination = track * TRACK_SIZE * 2 + side * TRACK_SIZE
            interleaved[destination : destination + TRACK_SIZE] = normalized[
                source : source + TRACK_SIZE
            ]
    return bytes(interleaved), bytes(normalized)


class DsdLoadingTest(unittest.TestCase):
    def test_loads_both_surfaces_and_reads_second_surface_files(self):
        raw_dsd, normalized = make_dsd_image()
        with tempfile.TemporaryDirectory() as directory:
            dsd_path = os.path.join(directory, "test.dsd")
            ssd_path = os.path.join(directory, "side1.ssd")
            output_dsd_path = os.path.join(directory, "roundtrip.dsd")
            with open(dsd_path, "wb") as file_p:
                file_p.write(raw_dsd)

            disk = acorn_dfs(dsd_path)

            self.assertEqual(
                [surface["title"] for surface in disk.disk_info],
                ["SIDE 0", "SIDE 1"],
            )
            self.assertEqual(disk.get_data(1, 0)[0], b"DATA")
            disk.write_ssd(1, ssd_path)
            with open(ssd_path, "rb") as file_p:
                self.assertEqual(file_p.read(), normalized[DISK_SIZE:])
            disk.write_dsd(0, output_dsd_path)
            with open(output_dsd_path, "rb") as file_p:
                self.assertEqual(file_p.read(), raw_dsd)

    def test_saves_consecutive_mmb_surfaces_as_interleaved_dsd(self):
        raw_dsd, normalized = make_dsd_image()
        with tempfile.TemporaryDirectory() as directory:
            mmb_path = os.path.join(directory, "test.mmb")
            dsd_path = os.path.join(directory, "pair.dsd")
            with open(mmb_path, "wb") as file_p:
                file_p.write(bytes(MMB_HEADER) + normalized)

            disk = acorn_dfs(mmb_path)
            disk.write_dsd(0, dsd_path)

            with open(dsd_path, "rb") as file_p:
                self.assertEqual(file_p.read(), raw_dsd)

    def test_opens_two_ssds_as_a_dsd(self):
        raw_dsd, normalized = make_dsd_image()
        with tempfile.TemporaryDirectory() as directory:
            side0_path = os.path.join(directory, "side0.ssd")
            side1_path = os.path.join(directory, "side1.ssd")
            dsd_path = os.path.join(directory, "pair.dsd")
            with open(side0_path, "wb") as file_p:
                file_p.write(normalized[:DISK_SIZE])
            with open(side1_path, "wb") as file_p:
                file_p.write(normalized[DISK_SIZE:])

            disk = acorn_dfs()
            disk.open_ssd_pair(side0_path, side1_path)

            self.assertEqual(
                [surface["title"] for surface in disk.disk_info],
                ["SIDE 0", "SIDE 1"],
            )
            self.assertEqual(disk.get_data(1, 0)[0], b"DATA")
            disk.write_dsd(0, dsd_path)
            with open(dsd_path, "rb") as file_p:
                self.assertEqual(file_p.read(), raw_dsd)

    def test_saves_standalone_ssd_with_blank_second_surface(self):
        _raw_dsd, normalized = make_dsd_image()
        with tempfile.TemporaryDirectory() as directory:
            ssd_path = os.path.join(directory, "single.ssd")
            dsd_path = os.path.join(directory, "single.dsd")
            with open(ssd_path, "wb") as file_p:
                file_p.write(normalized[:DISK_SIZE])

            disk = acorn_dfs(ssd_path)
            disk.write_dsd(0, dsd_path)
            saved_dsd = acorn_dfs(dsd_path)

            self.assertEqual(saved_dsd.disk_info[0]["title"], "SIDE 0")
            self.assertEqual(saved_dsd.disk_info[1]["title"], "")
            self.assertEqual(saved_dsd.disk_info[1]["file_count"], 0)
            self.assertEqual(saved_dsd.disk_info[1]["sector_count"], 800)

    def test_rejects_dsd_with_invalid_size(self):
        with self.assertRaises(ValueError):
            deinterleave_dsd(b"")


if __name__ == "__main__":
    unittest.main()
