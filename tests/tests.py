# Copyright (C) 2021  Max Wiklund
#
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import copy
import decimal
import unittest
import os

try:
    from unittest import mock
except ImportError:
    import mock

import image_sequence

TEXTRUES_ROOT = os.path.join(os.path.dirname(__file__), "textures")


def mock_join(*args):
    return "/".join(args)


class MockFile:
    def __init__(self, path):
        self.path = path
        self.is_file = lambda: True


@mock.patch("image_sequence.os.path.join", mock_join)
class TestImageSequence(unittest.TestCase):
    def test_parse_double_file_extension(self):
        seq = image_sequence.ImageSequence("/mock/geo_cache1.@@@@.bgeo.sc")
        expected_result = "/mock/geo_cache1.####.bgeo.sc"

        self.assertEqual(expected_result, seq.path)

    def test_raise_exception(self):
        with self.assertRaises(image_sequence.ImageSequenceParseError) as context:
            image_sequence.ImageSequence("")
        self.assertEqual('Input path ""', str(context.exception))

    def test_invalid_input_type(self):
        with self.assertRaises(AssertionError) as context:
            image_sequence.ImageSequence(MockFile(""))
        self.assertEqual("'path' expected str, not MockFile", str(context.exception))

    def test_add_frames(self):
        seq = image_sequence.ImageSequence("/mock/path/file_name.@@@.exr")
        seq.frames = [50, 10, 20, 30, 40, 40, 10]
        expected_result = [10, 20, 30, 40, 50]
        self.assertEqual(expected_result, seq.frames)

    def test_padding010(self):
        seq = image_sequence.ImageSequence("/mock/path/file_name.@@@.exr")
        expected_result = 3
        self.assertEqual(expected_result, seq.padding)

    def test_padding020(self):
        seq = image_sequence.ImageSequence("/mock/path/file_name.%02d.exr")
        expected_result = 2
        self.assertEqual(expected_result, seq.padding)

    def test_padding030(self):
        seq = image_sequence.ImageSequence("/mock/path/file_name.#####.exr")
        expected_result = 5
        self.assertEqual(expected_result, seq.padding)
        self.assertEqual("/mock/path/file_name.01001.exr", seq.eval_at_frame(1001))

    def test_eval_at_frame_no_frame(self):
        seq = image_sequence.ImageSequence("/mock/path/file_name.exr")
        expected_result = "/mock/path/file_name.exr"

        self.assertEqual(expected_result, seq.eval_at_frame(1001))

    def test_eval_at_frame(self):
        seq = image_sequence.ImageSequence("/mock/file_name.####.exr")
        expected_result = "/mock/file_name.1010.exr"

        self.assertEqual(expected_result, seq.eval_at_frame(1010))

    def test_eval_at_frame_float(self):
        seq = image_sequence.ImageSequence("/mock/file_name.####.exr")
        expected_result = "/mock/file_name.1010.0000045.exr"

        self.assertEqual(
            expected_result, seq.eval_at_frame(decimal.Decimal("1010.0000045"))
        )
        self.assertEqual("/mock/file_name.0010.21.exr", seq.eval_at_frame(10.21))

    def test_equals(self):
        a = image_sequence.ImageSequence("/mock/path/file_name.101.exr")
        b = image_sequence.ImageSequence("/mock/path/file_name.222.exr")
        expected_result = True

        self.assertEqual(expected_result, a == b)

    def test_not_equals020(self):
        a = image_sequence.ImageSequence("/mock/file_name.1001.exr")
        b = image_sequence.ImageSequence("/mock/path/file_name.1001.exr")
        expected_result = False

        self.assertEqual(expected_result, a == b)

    def test_set_format(self):
        seq = image_sequence.ImageSequence("/mock/path/file_name.1001.exr", "%")
        seq.set_format("{name}{ext}{frame}")
        expected_result = "file_name.exr.%04d"

        self.assertEqual(expected_result, seq.basename)

    def test_basename(self):
        seq = image_sequence.ImageSequence("/mock/path/file_name.1001.exr", "%")
        expected_result = "file_name.%04d.exr"

        self.assertEqual(expected_result, seq.basename)

    def test_dirname(self):
        seq = image_sequence.ImageSequence("/mock/path/file_name.1001.exr")
        expected_result = "/mock/path"

        self.assertEqual(expected_result, seq.dirname)

    def test_ext010(self):
        seq = image_sequence.ImageSequence("/mock/path/file_name.1001.exr")
        expected_result = ".exr"

        self.assertEqual(expected_result, seq.ext)

    def test_ext020(self):
        seq = image_sequence.ImageSequence("/mock/path/file_name.exr")
        expected_result = ".exr"

        self.assertEqual(expected_result, seq.ext)

    def test_set_ext(self):
        seq = image_sequence.ImageSequence("/mock/path/file_name.exr")
        seq.ext = ".jpg"
        expected_result = ".jpg"

        self.assertEqual(expected_result, seq.ext)

    def test_merge(self):
        a = image_sequence.ImageSequence("/mock/file_name.@@@.exr")
        a.frames = [10, 20, 30]
        b = image_sequence.ImageSequence("/mock/path/file_name.@@@.exr")
        b.frames = [30, 40, 50]

        a.merge(b)

        expected_result = [10, 20, 30, 40, 50]

        self.assertEqual(expected_result, a.frames)

    def test_get_paths(self):
        seq = image_sequence.ImageSequence("/mock/file_name.@@@.exr")
        seq.frames = [10, 20]

        expected_result = ["/mock/file_name.010.exr", "/mock/file_name.020.exr"]

        self.assertEqual(expected_result, seq.get_paths())

    def test_get_paths_with_offset(self):
        seq = image_sequence.ImageSequence("/mock/file_name.@@@.exr")
        seq.frames = [10.05, 20.00004]

        expected_result = [
            "/mock/file_name.025.05.exr",
            "/mock/file_name.035.00004.exr",
        ]

        self.assertEqual(expected_result, seq.get_paths(offset=15))

    def test_eval_at_frame010(self):
        seq = image_sequence.ImageSequence("/mock/file_name.%04d.exr")
        expected_result = "/mock/file_name.9999.exr"
        self.assertEqual(expected_result, seq.eval_at_frame(9999))

    def test_eval_at_frame020(self):
        seq = image_sequence.ImageSequence("/mock/file_name.exr")
        expected_result = "/mock/file_name.exr"
        self.assertEqual(expected_result, seq.eval_at_frame(9999))

    def test_find_frames_on_disk(self):
        path = os.path.join(TEXTRUES_ROOT, "char_dog_BUMP.%04d.exr")

        seq = image_sequence.ImageSequence(path)

        expected_result = [
            os.path.join(TEXTRUES_ROOT, "char_dog_BUMP.1002.exr"),
            os.path.join(TEXTRUES_ROOT, "char_dog_BUMP.1003.exr"),
        ]

        assert seq.find_frames_on_disk() == True

        self.assertEqual(expected_result, seq.get_paths())

    def test_format_with_padding_style(self):
        seq = image_sequence.ImageSequence("/mock/file_name.101.exr")
        expected_result1 = "/mock/file_name.###.exr"
        expected_result2 = "/mock/file_name.@@@.exr"
        expected_result3 = "/mock/file_name.*.exr"

        self.assertEqual(expected_result1, seq.format_with_padding_style("#"))

        self.assertEqual(expected_result2, seq.format_with_padding_style("@"))

        self.assertEqual(
            expected_result3, seq.format_with_padding_style("*", padding=1)
        )

    def test_format_with_padding_style_mov(self):
        seq = image_sequence.ImageSequence("/mock/file_name.mov")
        expected_result = "/mock/file_name.mov"
        self.assertEqual(expected_result, seq.format_with_padding_style("#"))

    def test_optional_format_with_padding_style(self):
        seq = image_sequence.ImageSequence("/mock/file_name.101.exr")
        expected_result1 = "/mock/file_name.ABC.exr"

        self.assertEqual(
            expected_result1, seq.optional_format_with_padding_style("ABC")
        )

        seq = image_sequence.ImageSequence("/mock/file_name.exr")
        expected_result2 = "/mock/file_name.exr"

        self.assertEqual(
            expected_result2, seq.optional_format_with_padding_style("ABC")
        )

    def test_name(self):
        seq = image_sequence.ImageSequence("/mock/file_name.101.exr", "%")
        seq.name = "new_file_name"

        expected_result_path = "/mock/new_file_name.%03d.exr"
        expected_result_name = "new_file_name"

        self.assertEqual(expected_result_name, seq.name)
        self.assertEqual(expected_result_path, seq.path)

    def test_set_frame_token(self):
        seq = image_sequence.ImageSequence("/mock/file_name.101.exr")
        seq.set_frame_token("$FRAME")

        expected_result = "/mock/file_name.$FRAME.exr"

        self.assertEqual(expected_result, seq.path)

    def test_houdini_frame_token(self):
        seq = image_sequence.ImageSequence("/mock/job_name_19234/v1/box.$F.bgeo.sc")
        expected_result = "/mock/job_name_19234/v1/box.#.bgeo.sc"

        self.assertEqual(expected_result, seq.path)

    def test_set_frame_token_none(self):
        seq = image_sequence.ImageSequence("/mock/file_name.101.exr")
        seq.set_frame_token("")
        expected_result = "/mock/file_name.exr"
        self.assertEqual(expected_result, seq.path)

    @mock.patch("image_sequence.os.path.exists", return_value=True)
    @mock.patch("image_sequence.os.scandir")
    def test_find_sequence_on_disk(self, scandir_mock, m):
        scandir_mock.return_value = [
            MockFile("/mock/file.999.exr"),
            MockFile("/mock/file.1001.exr"),
        ]
        seq = image_sequence.find_sequence_on_disk("/mock/file.#########.exr")

        expected_result_path = "/mock/file.###.exr"
        expected_result_frames = [999, 1001]

        self.assertEqual(expected_result_path, seq.path)
        self.assertEqual(expected_result_frames, seq.frames)

    def test_find_sequence_on_disk_failed(self):
        seq = image_sequence.find_sequence_on_disk("/mock/file.#.exr")
        expected_result = None
        self.assertEqual(expected_result, seq)

    @mock.patch("image_sequence.os.path.exists", return_value=True)
    @mock.patch("image_sequence.os.scandir")
    def test_find_sequence_on_disk_set_padding_style(self, scandir_mock, m):
        scandir_mock.return_value = [
            MockFile("/mock/file.999.exr"),
            MockFile("/mock/file.1001.exr"),
        ]
        seq = image_sequence.find_sequence_on_disk(
            "/mock/file.#.exr", padding_style="@"
        )

        expected_result_frames = [999, 1001]
        self.assertEqual(3, seq.padding)

        self.assertEqual(expected_result_frames, seq.frames)

    def test__getitem(self):
        seq = image_sequence.ImageSequence("/mock/file_name.101.exr")

        expected_result = "/mock/file_name.101.exr"
        self.assertEqual(expected_result, seq[0])

    @mock.patch("image_sequence.os.path.exists", return_value=True)
    @mock.patch("image_sequence.os.scandir")
    def test_find_sequence_on_disk_single_file(self, scandir_mock, m):
        scandir_mock.return_value = []

        expected_result_path = "/mock/file.abc"

        seq = image_sequence.find_sequence_on_disk("/mock/file.abc")

        self.assertEqual(expected_result_path, seq.path)

    def test_constructor_hash_padding(self):
        seq = image_sequence.ImageSequence(
            "/mock/file.09.exr", image_sequence.ImageSequence.HASH
        )

        expected_result1 = "/mock/file.##.exr"
        expected_result2 = "/mock/file.09.exr"

        self.assertEqual(expected_result1, seq.path)
        self.assertEqual(expected_result2, seq.eval_at_frame(9))

    def test_constructor_boost_padding(self):
        seq = image_sequence.ImageSequence(
            "/mock/file.09.exr", image_sequence.ImageSequence.BOOST
        )

        expected_result = "/mock/file.%02d.exr"

        self.assertEqual(expected_result, seq.path)

    def test_constructor_at_padding(self):
        seq = image_sequence.ImageSequence(
            "/mock/file.090.exr", image_sequence.ImageSequence.AT_SIGN
        )

        expected_result = "/mock/file.@@@.exr"

        self.assertEqual(expected_result, seq.path)

    def test_set_padding_hash(self):
        seq = image_sequence.ImageSequence(
            "/mock/file.exr", image_sequence.ImageSequence.HASH
        )
        seq.padding = 5

        expected_result = "/mock/file.#####.exr"

        self.assertEqual(expected_result, seq.path)

    def test_set_padding_style(self):
        seq = image_sequence.ImageSequence("/mock/file.101.exr", padding_style=">")
        expected_result = "/mock/file.>>>.exr"

        self.assertEqual(expected_result, seq.path)

    def test_create_success(self):
        seq = image_sequence.ImageSequence.new("/mock/file.101.exr", padding_style="%")
        expected_result = "/mock/file.%03d.exr"

        self.assertEqual(expected_result, seq.path)

    def test_create_padding_style_success(self):
        seq = image_sequence.ImageSequence.new("/mock/file.101.exr", padding_style="@")
        expected_result = "/mock/file.@@@.exr"

        self.assertEqual(expected_result, seq.path)

    def test_copy(self):
        a = image_sequence.ImageSequence("/mock/file.1001.exr")
        b = copy.copy(a)
        a.name = "hello"

        self.assertNotEqual(a.name, b.name)

    def test_copy_float_seq(self):
        a = image_sequence.ImageSequence("/mock/name.10.25.png")
        b = copy.copy(a)

        expected_result = ["/mock/name.10.25.png"]
        self.assertEqual(expected_result, b.get_paths())

    def test_endswith(self):
        seq = image_sequence.ImageSequence("/mock/file.1001.png")
        self.assertTrue(seq.endswith(".png"))
        self.assertFalse(seq.endswith((".mov", ".rat", ".exr")))

    def test_floating_frames(self):
        seq = image_sequence.ImageSequence("/mock/v41/rotatingTeapot.1009.70.bgeo.sc")
        self.assertEqual([decimal.Decimal("1009.70")], seq.frames)

        self.assertEqual(".####", seq.get_frame_token())

        self.assertEqual(["/mock/v41/rotatingTeapot.1009.70.bgeo.sc"], seq.get_paths())

        seq = image_sequence.ImageSequence("/mock/path/skin_bgeo_v023.####.bgeo.sc")
        self.assertEqual(
            "/mock/path/skin_bgeo_v023.0017.90.bgeo.sc",
            seq.eval_at_frame(decimal.Decimal("17.90")),
        )

    def test_add_floating_frame_range(self):
        seq = image_sequence.ImageSequence("/mock/file.%04d.png")
        seq.frames = [1001.7, 1002.6]
        expected_result = ["/mock/file.1001.7.png", "/mock/file.1002.6.png"]
        self.assertEqual(expected_result, seq.get_paths())

    def test_large_floating_frame(self):
        seq = image_sequence.ImageSequence(
            "/mock/char_collision.1029.4000000000001.bgeo.sc"
        )
        expected_result = ["/mock/char_collision.1029.4000000000001.bgeo.sc"]
        self.assertEqual(expected_result, seq.get_paths())

    def test_has_float_frames(self):
        seq = image_sequence.ImageSequence("/mock/path/file.103.78.bgeo.sc")
        self.assertTrue(seq.has_float_frames())
        seq = image_sequence.ImageSequence("/mock/path/file.1030.bgeo.sc")
        self.assertFalse(seq.has_float_frames())

    def test_append_frames(self):
        seq = image_sequence.ImageSequence("/mock/path/file.103.78.bgeo.sc")
        seq.frames.append(103.67)

        expected_result = [
            103.67,
            103.78,
        ]  # We expect that the float values are sorted.

        self.assertEqual(list(map(str, expected_result)), list(map(str, seq.frames)))

    def test_format_mixed_frames(self):
        seq = image_sequence.ImageSequence("/mock/path/file.##.bgeo.sc")
        seq.frames = [10, 10.6]

        expected_result = ["/mock/path/file.10.bgeo.sc", "/mock/path/file.10.6.bgeo.sc"]
        self.assertEqual(expected_result, seq.get_paths())

    def test_hidden_files(self):
        seq = image_sequence.ImageSequence("/mock/.assetName.mov")
        expected_result = "/mock/.assetName.mov"
        self.assertEqual(expected_result, seq.path)
        self.assertEqual(".assetName", seq.name)
        self.assertEqual(".mov", seq.ext)

    def test_flame_frame_exp(self):
        expected_path = "/mock/TVC_BSS_sh0010_FG01_v001.####.exr"
        expected_frames = [1001, 1089]
        seq = image_sequence.ImageSequence(
            "/mock/TVC_BSS_sh0010_FG01_v001.[1001-1089].exr",
        )

        self.assertEqual(expected_path, seq.path)
        self.assertEqual(expected_frames, seq.frames)
        self.assertEqual(seq.padding_style, image_sequence.ImageSequence.HASH)

    def test_flame_padding_style(self):
        seq = image_sequence.ImageSequence(
            "/mock/file.###.exr", padding_style=image_sequence.ImageSequence.FLAME
        )
        seq.frames = [101, 189]
        expected_result = "/mock/file.[101-189].exr"
        self.assertEqual(expected_result, seq.path)

        # Check what happens when you don't have a frame range.
        expected_result = "/mock/file.[0-0].exr"
        seq.frames = []
        self.assertEqual(expected_result, seq.path)

    def test_houdini_frame_exp(self):
        expected_path = "/mock/TVC_BSS_sh0010_FG01_v001.#.exr"
        seq = image_sequence.ImageSequence(
            "/mock/TVC_BSS_sh0010_FG01_v001.$F.exr",
        )

        self.assertEqual(expected_path, seq.path)
        self.assertEqual(seq.padding_style, image_sequence.ImageSequence.HASH)

    def test_houdini_padding_style(self):
        seq = image_sequence.ImageSequence(
            "/mock/file.###.exr", padding_style=image_sequence.ImageSequence.HOUDINI
        )
        expected_result = "/mock/file.$F3.exr"
        self.assertEqual(expected_result, seq.path)

    def test_houdini_ff_padding_style(self):
        seq = image_sequence.ImageSequence(
            "/mock/path/file.$FF.vdb",
            padding_style=image_sequence.ImageSequence.HOUDINI_FF,
        )
        expected_result = "/mock/path/file.10.4.vdb"
        expected_format = "/mock/path/file.$FF.vdb"

        self.assertEqual(expected_result, seq.eval_at_frame(10.4))
        self.assertEqual(expected_format, seq.path)

    def test_udim_padding(self):
        seq = image_sequence.ImageSequence(
            "/mock/path/file.1001.exr", padding_style=image_sequence.ImageSequence.UDIM
        )
        self.assertEqual("/mock/path/file.<UDIM>.exr", seq.path)

        seq = image_sequence.ImageSequence("/mock/path/file.<UDIM>.exr")
        self.assertEqual("/mock/path/file.####.exr", seq.path)
        self.assertEqual([], seq.frames)

    def test_support_special_characters(self):
        seq = image_sequence.ImageSequence("/mo1&(*%/path/%&^$%$£!_[30-40].[10-20].exr")
        expected_result = "%&^$%$£!_[30-40].##.exr"
        self.assertEqual(expected_result, seq.basename)
        self.assertEqual([10, 20], seq.frames)

    def test_seq_exists_no_frames(self):
        seq = image_sequence.ImageSequence(f"{TEXTRUES_ROOT}/test_maya_file.ma")
        self.assertTrue(seq.exists())

    def test_seq_exists_frames(self):
        seq = image_sequence.ImageSequence(f"{TEXTRUES_ROOT}/char_dog_BUMP.#.exr")
        self.assertTrue(seq.exists())

    def test_missing_frames(self):
        seq = image_sequence.ImageSequence(os.path.join(TEXTRUES_ROOT, "file.#.png"))
        seq.find_frames_on_disk()

        expected_result = [12]
        self.assertEqual(expected_result, seq.missing_frames)
