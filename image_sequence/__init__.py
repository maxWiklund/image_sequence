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
    r"(?P<name>[\w\-\[\]]+)"      # File name.
    r"(\.((?P<frame>\d+)|"        # Optional frame number.
    r"(?:%0(?P<token>\d+)d)|"     # Optional frame token e.g %04d
    r"(?P<udim><UDIM>)|"          # Optional udim token e.g <UDIM>
    r"(?P<padding>[#@]+)))?"      # Optional padding e.g @@ or ###
    r"(?P<ext>\.\w+(?:\.\w+)?)$"  # File extension.
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
    UDIM_STYLE = "<UDIM>"

    def __init__(self, path, padding_style=BOOST_FORMAT_STYLE):
        super(ImageSequence, self).__init__()
        self._pattern = "{name}{frame}{ext}"
        self._frames = []
        self._up_to_date = True
        self._padding = 0
        self._padding_style = padding_style  # This will be ignored if this is a udim.
        self.dirname = os.path.dirname(path)

        match = _RE_FILENAME.match(os.path.basename(path))
        self._data = match.groupdict("") if match else {}

        if self._data.get("frame"):
            self.frames.append(int(self._data["frame"]))
            self.padding = len(self._data["frame"])
        if self._data.get("udim"):
            self.padding_style = ImageSequence.UDIM_STYLE
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
        """str: Format pattern to represent frame range.

        Examples::
            >>>from image_sequence import ImageSequence
            >>>seq = ImageSequence("/mock/path/file_name.1001.exr")
            >>>seq.padding_style = ImageSequence.BOOST_FORMAT_STYLE
            >>>seq.path
            "/mock/path/file_name.%04d.exr"
            >>>seq.padding_style = "#"
            >>>seq.path
            "/mock/path/file_name.####.exr"

        """
        return self._padding_style

    @padding_style.setter
    def padding_style(self, value):
        self._padding_style = value
        if value == ImageSequence.UDIM_STYLE:
            self._padding = 4

        self._create_padding_format()

    def _create_padding_format(self):
        if self.padding_style == ImageSequence.BOOST_FORMAT_STYLE:
            self._data["frame"] = ".%0{}d".format(self._padding)
        elif self._padding_style == ImageSequence.UDIM_STYLE:
            self._data["frame"] = ".<UDIM>"
        else:
            self._data["frame"] = "." + self.padding_style * self.padding

    def set_format(self, pattern):
        """Set format pattern.

        Args:
            pattern (str): New format pattern.

        """
        self._pattern = pattern

    @property
    def basename(self):
        """str: Base name of file path."""
        return self._pattern.format(**self._data)

    @property
    def name(self):
        """str: Filename without frame token or extension. If you want the full name call `ImageSequence.basename()`."""
        return self._data["name"]

    @name.setter
    def name(self, value):
        self._data["name"] = value

    @property
    def ext(self):
        """str: File extension with dot."""
        return self._data["ext"]

    @ext.setter
    def ext(self, value):
        self._data["ext"] = value

    @property
    def path(self):
        """str: File path without frame formatting."""
        return os.path.join(self.dirname, self.basename)

    @property
    def frames(self):
        """list[int]: Frames in sequence."""
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
        """Merge frame range and padding with other object.

        Args:
            other (ImageSequence): Object to merge with.

        """
        self.frames += other.frames
        if other.padding > self.padding:
            self.padding = other.padding
        self._up_to_date = False

    def get_paths(self, offset=0):
        """Get file paths for all frames.

        Args:
            offset (int, optional): Number to offset frames with.

        Returns:
            list[str]: File paths for frame sequence.

        """
        path = self._get_path_for_formatting()
        if not self.frames:
            return [path]

        return [path % (frame + offset) for frame in self.frames]

    def eval_at_frame(self, frame):
        """Evaluate file path at specefyed frame and return corresponding frame.

        Args:
            frame (int): Frame number to generate string for.

        Returns:
            str: File path with specified frame.

        """
        path = self._get_path_for_formatting()
        if not self.padding:
            return path

        return path % frame

    def format_with_padding_style(self, style, padding=0):
        """Format path with custom padding type.

        Args:
            style (str): Padding style e.g (#, @, *).
            padding (int, optional):

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
        padding_tokens = style * (padding if padding else self.padding)
        data["frame"] = "." + padding_tokens if padding_tokens else ""
        return os.path.join(self.dirname, self._pattern.format(**data))

    def optional_frame_token_format(self, style):
        """Format path with custom padding type if padding is set.

        This is a great option if don't know if the file path hase frames or not.

        Args:
            style (str): Padding style e.g `(#, @, *)`.

        Examples::

            seq = ImageSequence("/mock/path/file.1001.exr")
            seq.optional_frame_token_format("$F")
            "/mock/path/file.$F.exr"

            seq = ImageSequence("/mock/path/file.exr")
            seq.optional_frame_token_format("<UDIM>")
            "/mock/path/file.exr"

        Returns:
            str: Formatted file path.

        """
        data = dict(self._data)
        padding_token = style if self.padding else ""
        data["frame"] = ".{}".format(padding_token) if padding_token else ""
        return os.path.join(self.dirname, self._pattern.format(**data))

    def set_custom_frame_token(self, token):
        """Set custom frame token e.g replace the frame number or symbols with a custom string.

        If padding style or padding is changed the frame toke will be replaced.

        Args:
            token (str): New token to set.

        """
        self._data["frame"] = "." + token if token else ""

    def find_frames_on_disk(self):
        """bool: Try to find frames on disk. True if frames found else False."""
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
        """int: First frame in sequence."""
        return self.frames[0] if self.frames else 0

    @property
    def end(self):
        """int: Last frame in sequence."""
        return self.frames[-1] if self.frames else 0

    def abstract_path_representation(self):
        """str: File path without frame padding."""
        return self.path.replace(self._data["frame"], ".$FRAME")

    def _get_path_for_formatting(self):
        """str: File path prepared for optional frame formatting."""
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

    def __bool__(self):
        return True

    def __copy__(self):
        obj = type(self)(self.path, padding_style=self.padding_style)
        obj._padding = self.padding
        obj.frames = self._frames
        obj._pattern = self._pattern
        return obj

    __nonzero__ = __bool__
