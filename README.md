# ImageP
 Image Processing – A minimalistic Python replacement for ImageJ.

ImageP was developed during an experiment for Fluid Physics (second year BSc course Applied Physics) to streamline data processing of a rotating cylindrical body of water. It was further developed into a proper application for future use and as a fun sideproject to learn PyQt.

Not only can it be used to process images, it can also open video files to track objects throughout time!

Please refer to the [documentation](https://github.com/JitseB/ImageP/blob/main/DOCUMENTATION.md) for a clear example on how to use the class properly.

A screenshot of the window can be seen below:
![window-screenshot](https://i.imgur.com/Pvk58Ff.png)

### The 'gui' function
Function that opens the GUI of ImageP. Returns array with calibrated clicked points relative to the origin.

Parameters:
- `path`: Path to image or video.
- `origin`: Change the origin to position xy (optional) (always in pixels!).
- `calibration`: The pixel calibration array (x and y pixel size) (optional).
- `unit`: The unit caused by the calibration array (pixels by default).
    If an array with the calibration values for the pixels was passed, it is recommended to also pass the corresponding unit to prevent confusion later on.
- `color`: The color used for the axis and points (optional) (black by default).

**VIDEO ONLY**:
- `frame`: The frame to start the program from (0 by default).
- `auto_progress`: Automatically progress to the next frame after clicking (false by default).
- `auto_progress_frame_interval`: Frames that are skipped when auto-progressing (1 frame per click by default).

`origin`, `calibration` and `unit` can also be defined from within the GUI.

When the GUI is opened, you can use `ctrl+z` to remove the previously clicked point and the arrows (left and right) can be used to move through the frames when a video file is passed through the `gui` function parameters.

## Copyright
ImageP is published under the [MIT license](https://github.com/JitseB/ImageP/blob/main/LICENSE.md).

Created by Jitse Boonstra in May 2021.
