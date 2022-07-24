![image_sequence Logo](logo.png)
Library for representing file sequences.

## Instantiate from a file path
```python
from image_sequence import ImageSequence

ImageSequence("/mock/path/file.1001.exr")
ImageSequence("/mock/path/file.%04d.exr")
ImageSequence("/mock/path/file.####.exr")
ImageSequence("/mock/path/file.<UDIM>.exr")
```

## Finding frame ranges on disk.
```python
from image_sequence import ImageSequence, find_sequence_on_disk

seq = ImageSequence("/mock/path/file.####.exr")
seq.find_frames_on_disk()
True

seq = find_sequence_on_disk("/mock/path/file.####.exr")
ImageSequence("/mock/path/file.####.exr")
```

## Frame padding
```python
from image_sequence import ImageSequence

seq = ImageSequence("/mock/path/file.101.exr")
print(seq.padding)
3
print(seq.path)
"/mock/path/file.%03d.exr"

seq.padding = 4
print(seq.path)
"/mock/path/file.%04d.exr"
```

## Updating the sequence
```python
from image_sequence import ImageSequence

seq = ImageSequence("/mock/path/file.1001.exr")
print(seq.path)
"/mock/path/file.%04d.exr"

print(seq.name)
"file"

seq.name = "newName"
print(seq.path)
"/mock/path/newName.%04d.exr"

print(seq.ext)
".exr"

seq.ext = ".jpg"
print(seq.path)
"/mock/path/newName.%04d.jpg"

seq.ext = ".exr"

print(seq.basename)
"newName.%04d.exr"

print(seq.dirname)
"/mock/path"

# Changing the padding style.
seq.padding_style = "@"
print(seq)
"/mock/path/newName.@@@@.exr"

# There is a built in UDIM type.
seq.padding_style = ImageSequence.UDIM_STYLE
print(seq.path)
"/mock/path/newName.<UDIM>.exr"

# The padding style can be set on the constructor.
seq = ImageSequence("/mock/path/fileName.1001.exr", padding_style=ImageSequence.UDIM_STYLE)
print(seq.path)
"/mock/path/fileName.<UDIM>.exr"
```

## Formatting Image sequence (None of these methods will affect the sequence object).
```python
from image_sequence import ImageSequence

seq = ImageSequence("/mock/path/file.1001.exr")
seq.eval_at_frame(9999)
"/mock/path/file.9999.exr"

print(seq.format_with_padding_style("#"))
"/mock/path/file.####.exr"

print(seq.format_with_padding_style("@", padding=2))
"/mock/path/file.@@.exr"

# The custom frame toke will only be set if frames exist.
print(seq.optional_frame_token_format("$F"))
"/mock/path/file.$F.exr"

seq = ImageSequence("/mock/path/file.exr")
print(seq.optional_frame_token_format("$F"))
"/mock/path/file.exr"
```

## Frame ranges
```python
from image_sequence import ImageSequence

seq = ImageSequence("/mock/path/file.1001.exr")
print(seq.frames)
[1001]

# Set frame range.
seq.frames = [10, 20, 30, 40]

# Querying frame range info
print(seq.start)
10

print(seq.end)
40
```

## Get List of File Paths
```python
from image_sequence import ImageSequence

seq = ImageSequence("/mock/path/file.###.exr")
seq.frames = [10, 20, 30, 40]
print(seq.get_paths())
[
    "/mock/path/file.010.exr",
    "/mock/path/file.020.exr",
    "/mock/path/file.030.exr",
    "/mock/path/file.040.exr"

]

# You can also offset the frame range.
print(seq.get_paths(offset=10))
[
    "/mock/path/file.020.exr",
    "/mock/path/file.030.exr",
    "/mock/path/file.040.exr",
    "/mock/path/file.050.exr"
]
```

## License
Apache License 2.0
