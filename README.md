# image_sequence
Library for representing file sequences.

## Usage

```python
from image_sequence import ImageSequence


# Ways to set frame padding.

# 1:
seq = ImageSequence("/mock/path/file.@@@.exr")

# 2:
seq = ImageSequence("/mock/path/file.###.exr")

# 3:
seq = ImageSequence("/mock/path/file.101.exr")


# Setting a frame range can be done in two ways.
seq = ImageSequence("/mock/path/file.1001.exr")

# 1:
seq.find_frames_on_disk()

# 2:
seq.frames = [10, 20, 30, ...]


# Getting paths
seq.get_paths()
[
    "/mock/path/file.1001.exr",
    "/mock/path/file.1002.exr",
    "/mock/path/file.1003.exr",
    "/mock/path/file.1004.exr",
    ...
]

seq.eval_at_frame(9999)
"/mock/path/file.9999.exr"


```