"""Check PNG structure where a correct hash alone would accept broken bytes."""

from pathlib import Path
import sys
import unittest
import zlib

from png_fixtures import chunk, png, rgba_pattern, SIGNATURE

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "brand-identity"))
from png_integrity import inspect_png


class PngEncodingTests(unittest.TestCase):
    def test_opaque_and_alpha_color_types(self):
        for depth, color, payload, has_alpha in (
            (1, 0, bytes([0, 0b10000000]), False),
            (8, 2, bytes([0, 255, 0, 0]), False),
            (8, 4, bytes([0, 255, 128]), True),
            (16, 6, bytes([0, 255, 255, 0, 0, 0, 0, 128, 128]), True),
        ):
            with self.subTest(depth=depth, color=color):
                self.assertEqual(inspect_png(png(1, 1, depth, color, payload)), (1, 1, has_alpha))

    def test_adam7_multiple_passes_and_packed_rows(self):
        # A 5 x 5 one-bit grayscale PNG has seven nonempty Adam7 passes.
        # At this size each pass row occupies one data byte plus its filter.
        rows = [1, 1, 1, 2, 1, 3, 2]
        pixels = b"".join(bytes([0, 0x80]) * count for count in rows)
        self.assertEqual(inspect_png(png(5, 5, 1, 0, pixels, interlace=1)), (5, 5, False))
        with self.assertRaisesRegex(ValueError, "length"):
            inspect_png(png(5, 5, 1, 0, pixels[:-2], interlace=1))

    def test_packed_rows_round_up_to_a_complete_byte(self):
        pixels = bytes([0, 255, 128, 0, 0, 128])
        self.assertEqual(inspect_png(png(9, 2, 1, 0, pixels)), (9, 2, False))
        with self.assertRaisesRegex(ValueError, "length"):
            inspect_png(png(9, 2, 1, 0, bytes([0, 255, 0, 128])))

    def test_invalid_dimensions_and_depth_are_rejected(self):
        for width, height, depth, color, reason in (
            (0, 1, 8, 6, "dimensions"),
            (1, 0, 8, 6, "dimensions"),
            (2**31, 1, 8, 6, "dimensions"),
            (1, 1, 4, 6, "header fields"),
            (1, 1, 8, 5, "color type"),
        ):
            with self.subTest(width=width, height=height, depth=depth, color=color):
                with self.assertRaisesRegex(ValueError, reason):
                    inspect_png(png(width, height, depth, color, b""))

    def test_indexed_palette_is_required_and_bounded_by_bit_depth(self):
        for metadata, reason in (
            ((), "missing indexed palette"),
            (((b"PLTE", bytes(9)),), "invalid PNG palette"),
            (((b"PLTE", bytes(4)),), "invalid PNG palette"),
            (((b"PLTE", bytes(6)), (b"PLTE", bytes(6))), "invalid PNG palette"),
        ):
            with self.subTest(metadata=metadata), self.assertRaisesRegex(ValueError, reason):
                inspect_png(png(1, 1, 1, 3, bytes([0, 0x80]), metadata=metadata))
        valid = png(1, 1, 1, 3, bytes([0, 0x80]), metadata=((b"PLTE", bytes(6)),))
        self.assertEqual(inspect_png(valid), (1, 1, False))

    def test_idat_can_span_multiple_adjacent_chunks(self):
        header = rgba_pattern()[:33]
        compressed = zlib.compress(bytes(17))
        first = chunk(b"IDAT", compressed[:4])
        second = chunk(b"IDAT", compressed[4:])
        end = chunk(b"IEND", b"")
        self.assertEqual(inspect_png(header + first + second + end), (4, 1, True))
        with self.assertRaisesRegex(ValueError, "invalid IDAT sequence"):
            inspect_png(header + first + chunk(b"tEXt", b"Note\0Test") + second + end)

    def test_extra_compressed_members_are_rejected(self):
        header = rgba_pattern()[:33]
        compressed = zlib.compress(bytes(17)) + zlib.compress(b"more")
        with self.assertRaisesRegex(ValueError, "length"):
            inspect_png(header + chunk(b"IDAT", compressed) + chunk(b"IEND", b""))

    def test_unknown_critical_chunk_stops_decoding(self):
        payload = rgba_pattern()
        header, image = payload[:33], payload[33:]
        with self.assertRaisesRegex(ValueError, "unexpected critical"):
            inspect_png(header + chunk(b"TEST", b"") + image)
        self.assertEqual(inspect_png(header + chunk(b"tESt", b"") + image), (4, 1, True))

    def test_missing_truncated_or_trailing_chunks_are_rejected(self):
        valid = rgba_pattern()
        for payload, reason in (
            (b"not a PNG", "missing PNG signature"),
            (SIGNATURE + chunk(b"IEND", b""), "IHDR"),
            (valid[:-12], "missing IEND"),
            (valid[:-1], "truncated PNG chunk"),
            (valid + b"after", "trailing PNG data"),
            (valid[:-12] + chunk(b"IEND", b"unexpected"), "invalid IEND"),
        ):
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                inspect_png(payload)
