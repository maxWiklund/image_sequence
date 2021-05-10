# -*- coding: utf-8 -*-
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


@mock.patch("image_sequence.os.path.join", mock_join)
class TestImageSequence(unittest.TestCase):
    def test_add_frames(self):
        seq = image_sequence.ImageSequence("/mock/path/file_name.@@@.exr")
        seq.frames = [50, 10, 20, 30, 40, 40, 10]
        expected_result = [10, 20, 30, 40, 50]
        self.assertEqual(
            expected_result, seq.frames
        )
    def test_new_sucess(self):
        seq = image_sequence.ImageSequence.new("/mock/path/file.1001.exr")
        expected_result = "/mock/path/file.%04d.exr"

        self.assertEqual(
            expected_result, seq.path
        )

    def test_new010(self):
        seq = image_sequence.ImageSequence.new("/mock/file.1001.a#$")
        expected_result = None

        self.assertEqual(
            expected_result, seq
        )

    def test_padding010(self):
        seq = image_sequence.ImageSequence("/mock/path/file_name.@@@.exr")
        expected_result = 3
        self.assertEqual(
            expected_result, seq.padding
        )

    def test_padding020(self):
        seq = image_sequence.ImageSequence("/mock/path/file_name.%02d.exr")
        expected_result = 2
        self.assertEqual(
            expected_result, seq.padding
        )

    def test_padding030(self):
        seq = image_sequence.ImageSequence("/mock/path/file_name.#####.exr", padding_style="#")
        expected_result = 5
        self.assertEqual(
            expected_result, seq.padding
        )
        self.assertEqual("/mock/path/file_name.01001.exr", seq.eval_at_frame(1001))

    def test_no_padding(self):
        expected_result = "/mock/path/file_name.exr"
        seq = image_sequence.ImageSequence("/mock/path/file_name.#####.exr")
        seq.padding = 0

        self.assertEqual(expected_result, seq.path)

    def test_equals(self):
        a = image_sequence.ImageSequence("/mock/path/file_name.101.exr")
        b = image_sequence.ImageSequence("/mock/path/file_name.222.exr")
        expected_result = True

        self.assertEqual(
            expected_result,
            a == b
        )

    def test_not_equals010(self):
        a = image_sequence.ImageSequence("/mock/path/file_name.1101.exr")
        b = image_sequence.ImageSequence("/mock/path/file_name.exr")
        expected_result = False

        self.assertEqual(
            expected_result,
            a == b
        )

    def test_not_equals020(self):
        a = image_sequence.ImageSequence("/mock/file_name.1001.exr")
        b = image_sequence.ImageSequence("/mock/path/file_name.1001.exr")
        expected_result = False

        self.assertEqual(
            expected_result,
            a == b
        )

    def test_set_format(self):
        seq = image_sequence.ImageSequence("/mock/path/file_name.1001.exr")
        seq.set_format("{name}{ext}{frame}")
        expected_result = "file_name.exr.%04d"

        self.assertEqual(
            expected_result,
            seq.basename
        )

    def test_basename(self):
        seq = image_sequence.ImageSequence("/mock/path/file_name.1001.exr")
        expected_result = "file_name.%04d.exr"

        self.assertEqual(
            expected_result,
            seq.basename
        )

    def test_dirname(self):
        seq = image_sequence.ImageSequence("/mock/path/file_name.1001.exr")
        expected_result = "/mock/path"

        self.assertEqual(
            expected_result,
            seq.dirname
        )

    def test_ext010(self):
        seq = image_sequence.ImageSequence("/mock/path/file_name.1001.exr")
        expected_result = ".exr"

        self.assertEqual(
            expected_result,
            seq.ext
        )

    def test_ext020(self):
        seq = image_sequence.ImageSequence("/mock/path/file_name.exr")
        expected_result = ".exr"

        self.assertEqual(
            expected_result,
            seq.ext
        )

    def test_set_ext(self):
        seq = image_sequence.ImageSequence("/mock/path/file_name.exr")
        seq.ext = ".jpg"
        expected_result = ".jpg"

        self.assertEqual(
            expected_result,
            seq.ext
        )

    def test_merge(self):
        a = image_sequence.ImageSequence("/mock/file_name.@@@.exr")
        a.frames = [10, 20, 30]
        b = image_sequence.ImageSequence("/mock/path/file_name.@@@.exr")
        b.frames = [30, 40, 50]

        a.merge(b)

        expected_result = [10, 20, 30, 40, 50]

        self.assertEqual(
            expected_result,
            a.frames
        )

    def test_get_paths(self):
        seq = image_sequence.ImageSequence("/mock/file_name.@@@.exr")
        seq.frames = [10, 20]

        expected_result = ["/mock/file_name.010.exr", "/mock/file_name.020.exr"]

        self.assertEqual(
            expected_result, seq.get_paths()
        )

    def test_eval_at_frame010(self):
        seq = image_sequence.ImageSequence("/mock/file_name.%04d.exr")
        expected_result = "/mock/file_name.9999.exr"
        self.assertEqual(
            expected_result, seq.eval_at_frame(9999)
        )

    def test_eval_at_frame020(self):
        seq = image_sequence.ImageSequence("/mock/file_name.exr")
        expected_result = "/mock/file_name.exr"
        self.assertEqual(
            expected_result, seq.eval_at_frame(9999)
        )

    def test_find_frames_on_disk(self):
        path = os.path.join(TEXTRUES_ROOT, "char_dog_BUMP.%04d.exr")

        seq = image_sequence.ImageSequence(path)

        expected_result = [
            os.path.join(TEXTRUES_ROOT, "char_dog_BUMP.1002.exr"),
            os.path.join(TEXTRUES_ROOT, "char_dog_BUMP.1003.exr")
        ]

        assert seq.find_frames_on_disk() == True

        self.assertEqual(
            expected_result,
            seq.get_paths()
        )

    def test_set_padding_style010(self):
        expected_result = "/mock/file.####.rat"

        seq = image_sequence.ImageSequence("/mock/file.4444.rat", padding_style="#")
        self.assertEqual(expected_result, seq.path)

    def test_set_padding_style020(self):
        expected_result = "/mock/file.####.rat"

        seq = image_sequence.ImageSequence("/mock/file.4444.rat")
        seq.padding_style = "#"
        self.assertEqual(expected_result, seq.path)

    def test_set_padding_style_copy(self):
        expected_result = "/mock/file.@@@@.rat"

        seq = image_sequence.ImageSequence("/mock/file.4444.rat", "@")
        new_seq = copy.copy(seq)

        self.assertEqual(expected_result, new_seq.path)

    def test_format_with_padding_style(self):
        seq = image_sequence.ImageSequence("/mock/file_name.101.exr")
        expected_result1 = "/mock/file_name.###.exr"
        expected_result2 = "/mock/file_name.@@@.exr"
        expected_result3 = "/mock/file_name.*.exr"

        self.assertEqual(
            expected_result1, seq.format_with_padding_style("#")
        )

        self.assertEqual(
            expected_result2, seq.format_with_padding_style("@")
        )

        self.assertEqual(
            expected_result3, seq.format_with_padding_style("*", padding=1)
        )

    def test_name(self):
        seq = image_sequence.ImageSequence("/mock/file_name.101.exr")
        seq.name = "new_file_name"

        expected_result_path = "/mock/new_file_name.%03d.exr"
        expected_result_name = "new_file_name"

        self.assertEqual(
            expected_result_name,
            seq.name
        )
        self.assertEqual(
            expected_result_path,
            seq.path
        )

    def test_set_custom_frame_token(self):
        expected_result = "/mock/path/file.<UDIM>.exr"
        seq = image_sequence.ImageSequence("/mock/path/file.1001.exr")
        seq.set_custom_frame_token("<UDIM>")

        self.assertEqual(expected_result, seq.path)

    def test_abstract_path_representation_010(self):
        expected_result = "/mock/file_name.$FRAME.exr"
        seq = image_sequence.ImageSequence("/mock/file_name.101.exr")

        self.assertEqual(
            expected_result, seq.abstract_path_representation()
        )

    def test_find_sequence_on_disk_func(self):
        expected_result = [
            os.path.join(TEXTRUES_ROOT, "char_dog_DIFFUSE.1001.exr"),
            os.path.join(TEXTRUES_ROOT, "char_dog_DIFFUSE.1002.exr")
        ]

        path = os.path.join(TEXTRUES_ROOT, "char_dog_DIFFUSE.#.exr")
        seq = image_sequence.find_sequence_on_disk(path)

        self.assertEqual(expected_result, seq.get_paths())
