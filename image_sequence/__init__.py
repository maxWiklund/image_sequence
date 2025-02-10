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
from __future__ import annotations
from typing import Union, Tuple, List, Optional, Iterator
from decimal import Decimal
import re
import os

try:
    import importlib.metadata

    __version__ = importlib.metadata.version("image_sequence")
except ImportError:
    import importlib_metadata

    __version__ = importlib_metadata.version("image_sequence")


# fmt: off
_RE_FILENAME = re.compile(
    r"(?P<name>(\.)?[^\.]+)"                          # File name.
    r"(\.((?P<frame>\d+(?P<float>\.\d+)?)|"           # Optional frame number.
    r"(?:%0(?P<token>\d+)d)|"                         # Optional frame token e.g %04d
    r"(?P<udim><UDIM>)|"                              # Optional udim token e.g <UDIM>
    r"(?:\[(?P<flame>\d+-\d+)\])|"                    # Optional flame padding e.g [1-10]
    r"(?P<padding>[#@]+)|"                            # Optional padding e.g (@@ or ###
    r"(?P<hip_frame>\$[fF]+(?P<hip_padding>\d)?)))?"  # Optional houdini padding e.g $F
    r"(?P<ext>\.\w+(\.\w+)?)$"                        # File extension.
)
# fmt: on

_RE_FLOAT_SUFFIX = re.compile(r"(?P<decimal>\.\d+)")

FRAME_TOKEN = "<FRAME>"
"""str: Frame token to replace."""

Frame = Union[int, float, Decimal]


class ImageSequenceParseError(Exception):
    """Exception to raise if file path can not be parsed."""


def find_sequence_on_disk(path: str, **kwargs) -> Optional[ImageSequence]:
    """Create  if file is valid.

    Args:
        path: File path.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        Found sequence or None.

    """
    seq = ImageSequence.new(path, **kwargs)
    if seq and (seq.find_frames_on_disk() or os.path.exists(seq.path)):
        return seq
    return None


class ImageSequence(object):
    """Class for representing a file sequence.

    Examples::

        from image_sequence import ImageSequence
        seq = ImageSequence("/mock/path/file_name.1001.exr")
        seq.find_frames_on_disk()
        True

    """

    BOOST = "%"
    HASH = "#"
    AT_SIGN = "@"
    FLAME = "flame"
    HOUDINI = "houdini"
    HOUDINI_FF = "$FF"
    UDIM = "<UDIM>"

    def __init__(
        self,
        path: str,
        padding_style: str = HASH,
        _match: Optional[re.Match] = None,
    ):
        """Parse file name and setup class.

        Args:
            path: File path.
            padding_style (optional): Padding style defaults to boost style
                formatting (%04d).

        Raises:
            AssertionError: If 'path' passed as anything but a string.
            ImageSequenceParseError: Failed to parse input file path.

        """
        super().__init__()
        assert (
            isinstance(path, str) == True
        ), f"'path' expected str, not {type(path).__name__}"
        self._pattern = "{name}{frame}{ext}"
        self._frames = []
        self._last_frame_hash = hash(str(self._frames))
        self._up_to_date = True
        self._padding = 0

        self._padding_style = padding_style
        self.dirname = os.path.dirname(path)

        ####################
        #
        # Eval file name and split it up in sections.
        #
        match = _match or _RE_FILENAME.match(os.path.basename(path))
        self._data = match.groupdict("") if match else {}

        if self._data.get("frame"):
            frame = self._data["frame"]
            float_value = self._data.get("float", "")
            self._frames.append(Decimal(frame) if float_value else int(frame))
            self.padding = len(frame.replace(float_value, ""))
        elif self._data.get("token"):
            self.padding = int(self._data["token"])
        elif self._data.get("padding"):
            self.padding = len(self._data.get("padding"))
        elif self._data.get("flame"):
            self.frames = list(map(int, self._data["flame"].split("-")))
            self.padding = len(str(self.start()))
        elif self._data.get("hip_frame"):
            self.padding = int(self._data.get("hip_padding") or 1)
        elif self._data.get("udim"):
            self.padding = 4
        if not self._data:
            raise ImageSequenceParseError(f'Input path "{path}"')

    @classmethod
    def new(cls, path: str, **kwargs) -> Optional[ImageSequence]:
        """Create sequence if path is valid.

        Args:
            path (str): File path.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Sequence object. None is returned if path was invalid.

        Raises:
            AssertionError: If 'path' passed as anything but a string.

        """
        assert isinstance(path, str), f"'path' expected str, not {type(path).__name__}"
        match = _RE_FILENAME.match(os.path.basename(path))
        if match:
            return cls(path, _match=match, **kwargs)
        return None

    def _format_frame(self, path: str, frame: Frame, offset: int) -> str:
        """Format frame number.

        Args:
            path: File path to format.
            frame: Frame object to use for formating.
            offset: Offset number.

        Returns:
            Formatted path.

        """
        number = _RE_FLOAT_SUFFIX.sub("", str(frame))
        decimal = (
            _RE_FLOAT_SUFFIX.search(str(frame)).group("decimal")
            if _RE_FLOAT_SUFFIX.search(str(frame))
            else ""
        )
        frame_num = f"%0{self._padding}d{decimal}" % (int(number) + offset)
        return path.replace(FRAME_TOKEN, frame_num)

    def endswith(self, arg: Union[Tuple[str, ...], str]) -> bool:
        """Check if image sequence endswith args.

        Args:
            arg: String or strings to check.

        Returns:
            True if match found.

        """
        return self.path.endswith(arg)

    @property
    def missing_frames(
        self,
    ) -> List[int]:
        """List of missing frames if we consider the sequence to have one-step intervals.

        Returns:
            Missing frames.

        """
        if self.has_float_frames():
            # We can't predict the step value of float numbers.
            return []

        return list(set(range(self.start(), self.end())).difference(set(self.frames)))

    @property
    def padding(self) -> int:
        """Get frame padding number.

        Returns:
            Padding number.

        """
        return self._padding

    @padding.setter
    def padding(self, value: int) -> None:
        self._padding = value
        if value < 1:
            self._data["frame"] = ""
        else:
            self._create_padding_format()

    @property
    def padding_style(self) -> str:
        """Set or get padding style.

        Examples::

            seq = ImageSequence("/path/file.101.exr")
            seq.path
            "/path/file.###.exr"
            seq.padding_style = ImageSequence.BOOST
            seq.path
            "/path/file.%03d.exr"

        Returns:
            Padding style.

        """
        return self._padding_style

    @padding_style.setter
    def padding_style(self, value: str) -> None:
        self._padding_style = value
        self._create_padding_format()

    def has_float_frames(self) -> bool:
        """Check if any frame is float.

        Returns:
            True if any frame is float.

        """
        return not all(isinstance(f, int) for f in self.frames)

    def set_format(self, pattern: str) -> None:
        """Set file name format template.

        Default pattern "{name}{frame}{ext}".

        Args:
            pattern: Name pattern.

        """
        self._pattern = pattern

    def get_format(self) -> str:
        """Get format template string.

        Returns:
            Format template string.

        """
        return self._pattern

    @property
    def basename(self) -> str:
        """Sequence base name e.g file name without path.

        Returns:
            Basename of sequence.

        """
        return self._pattern.format(**self._data)

    @property
    def name(self) -> str:
        """Filename without frame or file extension.

        Returns:
            File name.

        """
        return self._data["name"]

    @name.setter
    def name(self, value: str) -> None:
        self._data["name"] = value

    @property
    def ext(self) -> str:
        """File extension (must include dot).

        Returns:
            File extension.

        """
        return self._data["ext"]

    @ext.setter
    def ext(self, value: str) -> None:
        self._data["ext"] = value

    @property
    def path(self) -> str:
        """Get formatted file path with frame toke placeholder.

        Examples::

            seq = ImageSequence("/path/file.099.jpg")
            seq.path
            "/path/file.###.jpg"

        Returns:
            File path.

        """
        return os.path.join(self.dirname, self.basename)

    @property
    def frames(self) -> List[Frame]:
        """Get frames from image sequence.

        Returns:
            Frame numbers.

        """
        if not self._up_to_date or hash(str(self._frames)) != self._last_frame_hash:
            # We only want to sort items if they are not sorted.
            self._frames = list(set(self._frames))
            self._frames.sort()
            self._last_frame_hash = hash(str(self._frames))
            self._up_to_date = True

        return self._frames

    @frames.setter
    def frames(self, value: List[Frame]) -> None:
        # A user has appended or removed frames.
        self._up_to_date = False
        self._frames = value

        if self.padding_style == ImageSequence.FLAME:
            # Reevaluate padding style to pick up flame style padding.
            # The flame style padding needs the start and end frame e.g "[1-10]"
            self._create_padding_format()

    def _create_padding_format(self) -> None:
        """Generate padding string."""
        if self.padding_style == ImageSequence.BOOST:
            self._data["frame"] = ".%0{}d".format(self._padding)
        elif self._padding_style == ImageSequence.FLAME:
            self._data["frame"] = f".[{self.start()}-{self.end()}]"
        elif self.padding_style == ImageSequence.HOUDINI_FF:
            self._data["frame"] = ".$FF"
        elif self._padding_style == ImageSequence.HOUDINI:
            self._data["frame"] = f".$F{self.padding or ''}"
        elif self._padding_style == ImageSequence.UDIM:
            self._data["frame"] = ".<UDIM>"
        else:
            self._data["frame"] = "." + self.padding_style * self.padding

    def set_frame_token(self, token: str) -> None:
        """Warning! This is dangerous as FU#K.

        The class methods exists to allow users to set custom frame tokens.
        The reason this is dangerous is that we can't guarantee that
        frame token will remain. If you update the padding or do anything else
        that might trigger ``ImageSequence._create_padding_format`` your
        custom frame token will be lost.

        If you look at the example section you can see edge cases where it
        might be handy to use.

        Args:
            token: String to replace frame token.

        Examples::

            seq = ImageSequence("/mock/path/file_name.1001.exr")
            seq.set_frame_token("<UDIM>")
            print(seq.path)
            "/mock/path/file_name.<UDIM>.exr")

        """
        self._data["frame"] = "." + token if token else ""

    def get_frame_token(self) -> str:
        """If element has frame token return it else empty string.

        Returns:
            Frame token.

        """
        return self._data.get("frame", "")

    def merge(self, other: ImageSequence) -> None:
        """Merge element with other element.

        Args:
            other: Element to merge with.

        """
        self.frames += other.frames
        self._up_to_date = False
        if other.padding < self.padding:
            self.padding = other.padding

    def get_paths(self, offset: int = 0) -> List[str]:
        """Formatted file paths.

        Args:
            offset (optional): Frame offset.

        Examples::

            seq = ImageSequence("/path/file.##.exr")
            seq.frames = [10, 20]
            seq.get_paths()
            ["/path/file.10.exr", "/path/file.20.exr"]
            seq.get_paths(100)
            ["/path/file.110.exr", "/path/file.120.exr"]

        Returns:
            Formatted file paths.

        """
        path = self._get_path_for_formatting()
        if not self.frames:  # This sorte the range if it is not done.
            return [path]

        return [self._format_frame(path, frame, offset) for frame in self.frames]

    def eval_at_frame(self, frame: Union[int, float]) -> str:
        """Format file path with frame.

        Args:
            frame: Frame number.

        Examples::

            seq = ImageSequence("/path/file.1001.jpg")
            seq.eval_at_frame(9999)
            "/path/file.9999.jpg"

        Returns:
            Evaluated file path.

        """
        path = self._get_path_for_formatting()
        if not self.padding:
            return path
        return self._format_frame(path, frame, offset=0)

    def format_with_padding_style(self, style: str, padding: int = 0) -> str:
        """Format path with custom padding type.

        Args:
            style: Padding style e.g `(#, @, *)`.
            padding (optional): Padding number.

        Examples::

            seq = ImageSequence("/mock/path/file.1001.exr")
            seq.format_with_padding_style("#")
            "/mock/path/file.####.exr"
            seq.format_with_padding_style("@", padding=2)
            "/mock/path/file.@@.ex"

        Returns:
            Formatted file path.

        """
        data = dict(self._data)
        padding_token = style * (padding if padding else self.padding)
        data["frame"] = "." + padding_token if padding_token else ""
        return os.path.join(self.dirname, self._pattern.format(**data))

    def optional_format_with_padding_style(self, style: str) -> str:
        """Format path with custom padding type.

        Args:
            style: Padding style e.g `(#, @, *)`.

        Examples::

            seq = ImageSequence("/mock/path/file.1001.exr")
            seq.format_with_padding_style("<UDIM>")
            "/mock/path/file.<UDIM>.exr"

            seq = ImageSequence("/mock/path/file.exr")
            seq.format_with_padding_style("<UDIM>")
            "/mock/path/file.exr"

        Returns:
            Formatted file path.

        """
        data = dict(self._data)
        padding_token = style if self.padding else ""
        data["frame"] = ".{}".format(padding_token) if padding_token else ""
        return os.path.join(self.dirname, self._pattern.format(**data))

    def find_frames_on_disk(self) -> bool:
        """Find frames on disk and append to sequence object.

        Returns:
            True if frames found else False.

        """
        if not self.dirname:
            return False

        if not self._data.get("frame"):
            return False

        if not os.path.exists(self.dirname):
            return False

        # Set the padding to the lowest found padding number in sequence range.
        old_padding = self.padding
        self._padding = float("inf")
        for path in os.scandir(self.dirname):
            if not path.is_file():
                continue

            element = ImageSequence.new(path.path)
            if not element:
                continue

            if (
                self.abstract_path_representation()
                == element.abstract_path_representation()
            ):
                self.merge(element)

        # No frames found revert to old padding.
        if self.padding == float("inf"):
            self.padding = old_padding

        return bool(self.frames)

    def start(self) -> Frame:
        """Get first frame in frame range.

        Returns:
            Start frame.

        """
        return self.frames[0] if self.frames else 0

    def end(self) -> Frame:
        """Get last frame in frame range.

        Returns:
            End frame.

        """
        return self.frames[-1] if self.frames else 0

    def abstract_path_representation(self) -> str:
        """Abstract representation of element that is padding agnostic.

        When we compare elements padding length and padding style have to be
        removed from comparison. This method create an abstract representation
        of the file path without taking padding into account.

        Returns:
            File path without frame padding.

        """
        return self.path.replace(self._data["frame"], f".{FRAME_TOKEN}")

    def _get_path_for_formatting(self) -> str:
        """Get formatting string.

        Returns:
            File path prepared for formatting.

        """
        data = dict(self._data)
        if data.get("frame"):
            data["frame"] = f".{FRAME_TOKEN}"

        return os.path.join(self.dirname, self._pattern.format(**data))

    def exists(self) -> bool:
        """Check if sequence exists on disk.

        Returns:
            True if sequence exists on disk.

        """
        self.find_frames_on_disk()
        return os.path.exists(self.eval_at_frame(self.start()))

    def __eq__(self, other: ImageSequence) -> bool:
        """Compare element.

        Args:
            other: Object to compare to.

        Returns:
            True if elements are equal else False.

        """
        return (
            self.abstract_path_representation() == other.abstract_path_representation()
        )

    def __iter__(self) -> Iterator[str]:
        """Iterate over file paths.

        Returns:
            Iterate object.

        """
        return iter(self.get_paths())

    def __len__(self) -> int:
        """Number of frames.

        Returns:
            Number of frames.

        """
        return len(self.frames)

    def __repr__(self) -> str:
        """Print representation of object.

        Returns:
            Class string representation

        """
        return '{cls}(path="{path}"'.format(cls=self.__class__.__name__, path=self.path)

    def __str__(self) -> str:
        """File path with frame placeholder

        Returns:
            File path.

        """
        return self.path

    def __hash__(self) -> int:
        """Hash operator overload."

        Returns:
            Hash string.

        """
        return hash(self.path)

    def __bool__(self) -> bool:
        """Boolean operator overload (this is a python3 operator).

        Returns:
            True.

        """
        return True

    def __getitem__(self, index: int) -> str:
        """Get formated path from index.

        Args:
            index: Frame list index.

        Raises:
            IndexError: Frame list index out of range.

        Returns:
            Formated path.

        """
        try:
            return self.get_paths()[index]
        except IndexError:
            raise IndexError("index out of range")

    def __copy__(self) -> ImageSequence:
        """Copy operator overload.

        Returns:
            New Sequence.

        """
        obj = type(self)(self.path, self.padding_style)
        obj._padding = self.padding
        obj.frames = self.frames
        obj._pattern = self._pattern
        return obj
