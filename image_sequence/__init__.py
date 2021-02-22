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


class ImageSequence(object):
    """Class for representing a file sequence.

    Examples:
        >>>from image_sequence import ImageSequence
        >>>seq = ImageSequence("/mock/path/file_name.1001.exr")
        >>>seq.find_frames_on_disk()
        True

    """
    def __init__(self, path):
        super(ImageSequence, self).__init__()
        self._pattern = "{name}{frame}{ext}"
        self._frames = []
        self._up_to_date = True
        self._padding = 0
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

    @property
    def padding(self):
        return self._padding

    @padding.setter
    def padding(self, value):
        self._padding = value
        self._data["frame"] = ".%0{}d".format(self._padding)

    def set_format(self, pattern):
        self._pattern = pattern

    @property
    def basename(self):
        return self._pattern.format(**self._data)

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
        self._up_to_date = False

    def get_paths(self, offset=0):
        if not self.frames:
            return [self.path]

        return [self.path % (frame + offset) for frame in self.frames]

    def eval_at_frame(self, frame):
        if not self.padding:
            return self.path

        return self.path % frame

    def find_frames_on_disk(self):
        """bool: True if frames found else False."""
        if not self.dirname:
            return False

        if not self._data.get("frame"):
            return False

        for path in scandir(self.dirname):
            if not path.is_file():
                continue

            element = ImageSequence(path.path)
            if self == element:
                self.merge(element)

        return True

    def __eq__(self, other):
        return self.path == other.path

    def __iter__(self):
        return iter(self.get_paths())

    def __len__(self):
        return len(self.frames)

    def __repr__(self):
        return self.path

    def __str__(self):
        return self.path
