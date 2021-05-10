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
import re
import os

try:
    from os import scandir
except ImportError:
    from scandir import scandir


__version__ = "0.1.0"

_RE_FILENAME = re.compile(
    r"(?P<name>[\w\-\[\]]+)"   # File name.
    r"(\.((?P<frame>\d+)|"     # Optionaly frame number.
    r"(?:%0(?P<token>\d+)d)|"  # Optionaly frame token e.g %04d
    r"(?P<padding>[#@]+)))?"   # Optionaly padding e.g (@@ or ###
    r"(?P<ext>\.\w+)$"         # File extension.
)


def find_sequence_on_disk(path):
    """Create ImageSequence object and find coresponding frames.

    Args:
        path (str): File path.

    Returns:
        <ImageSequence> or None: Image sequence object with frames.

    """
    seq = ImageSequence.new(path)

    if seq and (seq.find_frames_on_disk() or os.path.exists(seq.path)):
        return seq
    return seq


class ImageSequence(object):
    """Class for representing a file sequence.

    Examples:
        >>>from image_sequence import ImageSequence
        >>>seq = ImageSequence("/mock/path/file_name.1001.exr")
        >>>seq.find_frames_on_disk()
        True

    """
    BOOST_FORMAT_STYLE = "%"

    def __init__(self, path, padding_style=BOOST_FORMAT_STYLE):
        super(ImageSequence, self).__init__()
        self._pattern = "{name}{frame}{ext}"
        self._frames = []
        self._up_to_date = True
        self._padding = 0
        self._padding_style = padding_style
        self.dirname = os.path.dirname(path)

        match = _RE_FILENAME.match(os.path.basename(path))
        self._data = match.groupdict("") if match else {}

        if self._data.get("frame"):
            self.frames.append(int(self._data["frame"]))
            self.padding = len(self._data["frame"])
        elif self._data.get("token"):
            self.padding = int(self._data["token"])
        elif self._data.get("padding"):
            self.padding = len(self._data.get("padding"))

    @classmethod
    def new(cls, path, padding_style=BOOST_FORMAT_STYLE):
        if _RE_FILENAME.match(os.path.basename(path)):
            return cls(path, padding_style)
        return None

    @property
    def padding(self):
        return self._padding

    @padding.setter
    def padding(self, value):
        self._padding = value
        if value < 1:
            self._data["frame"] = ""
        else:
            self._create_padding_format()

    @property
    def padding_style(self):
        return self._padding_style

    @padding_style.setter
    def padding_style(self, value):
        self._padding_style = value
        self._create_padding_format()

    def _create_padding_format(self):
        if self.padding_style == ImageSequence.BOOST_FORMAT_STYLE:
            self._data["frame"] = ".%0{}d".format(self._padding)
        else:
            self._data["frame"] = "." + self.padding_style * self.padding

    def set_format(self, pattern):
        self._pattern = pattern

    @property
    def basename(self):
        return self._pattern.format(**self._data)

    @property
    def name(self):
        return self._data["name"]

    @name.setter
    def name(self, value):
        self._data["name"] = value

    @property
    def ext(self):
        return self._data["ext"]

    @ext.setter
    def ext(self, value):
        self._data["ext"] = value

    @property
    def path(self):
        return os.path.join(self.dirname, self.basename)

    @property
    def frames(self):
        if not self._up_to_date:
            self._frames = list(set(self._frames))
            self._frames.sort()
            self._up_to_date = True

        return self._frames

    @frames.setter
    def frames(self, value):
        self._up_to_date = False
        self._frames = value

    def merge(self, other):
        self.frames += other.frames
        if other.padding > self.padding:
            self.padding = other.padding
        self._up_to_date = False

    def get_paths(self, offset=0):
        path = self._get_path_for_formatting()
        if not self.frames:
            return [path]

        return [path % (frame + offset) for frame in self.frames]

    def eval_at_frame(self, frame):
        path = self._get_path_for_formatting()
        if not self.padding:
            return path

        return path % frame

    def format_with_padding_style(self, style, padding=0):
        """Format path with custom padding type.

        Args:
            style (str): Padding style e.g (#, @, *).
            padding (:obj: `int`, optional):

        Examples:
            >>>from image_sequence import ImageSequence
            >>>seq = ImageSequence("/mock/path/file.1001.exr")
            >>>seq.format_with_padding_style("#")
            '/mock/path/file.####.exr'
            >>>seq.format_with_padding_style("@", padding=2)
            '/mock/path/file.@@.exr

        Returns:
            str: Formated file path.

        """
        data = dict(self._data)
        data["frame"] = "." + style * (padding if padding else self.padding)
        return os.path.join(self.dirname, self._pattern.format(**data))

    def set_custom_frame_token(self, token):
        self._data["frame"] = "." + token if token else ""

    def find_frames_on_disk(self):
        """bool: True if frames found else False."""
        if not self.dirname:
            return False

        if not self._data.get("frame"):
            return False

        if not os.path.exists(self.dirname):
            return False

        for path in scandir(self.dirname):
            if not path.is_file():
                continue

            element = ImageSequence.new(path.path)

            # Filter out file names that we can't parse.
            if not element:
                continue

            if self.abstract_path_representation() == element.abstract_path_representation():
                self.merge(element)

        return bool(self.frames)

    @property
    def start(self):
        return self.frames[0] if self.frames else 0

    @property
    def end(self):
        return self.frames[-1] if self.frames else 0

    def abstract_path_representation(self):
        """str: File path without frame padding."""
        return self.path.replace(self._data["frame"], ".$FRAME")

    def _get_path_for_formatting(self):
        """str: """
        data = dict(self._data)
        if data.get("frame"):
            data["frame"] = ".%0{}d".format(self.padding)
        return os.path.join(self.dirname, self._pattern.format(**data))

    def __eq__(self, other):
        return self.abstract_path_representation() == other.abstract_path_representation()

    def __ne__(self, other):
        return not self == other

    def __iter__(self):
        return iter(self.get_paths())

    def __len__(self):
        return len(self.frames)

    def __repr__(self):
        return self.path

    def __str__(self):
        return self.path

    def __nonzero__(self):
        return True

    def __bool__(self):
        return True

    def __copy__(self):
        obj = type(self)(self.path, padding_style=self.padding_style)
        obj._padding = self.padding
        obj.frames = self._frames
        obj._pattern = self._pattern
        return obj
