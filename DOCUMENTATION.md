# ImageP Documentation
In this documentation you will find an extensive example of how to use the ImageP class.

ImageP was created as a minimalistic replacement for ImageJ for automization reasons. ImageP can be used in a Jupyter notebook and has an easy to use movable origin.

## Dependencies
This library depends on [Python OpenCV](https://pypi.org/project/opencv-python/) and [pyqtgraph](https://pypi.org/project/pyqtgraph/).

## Processing an image
For this example, we will use an image of a protractor. This way, we know for sure that the measurements of the class are correct.

![protractor](https://media.s-bol.com/RZN8OvEkxOY/550x370.jpg)

## Loading in the image, open the GUI and set the origin
```Python
import matplotlib.pyplot as plt
import numpy as np

from imagep import gui


# Returns array of all clicked points. In this case, there is only one, which we will select.
origin = gui('./test.jpg', color='black')[0]
```

This will show the GUI:
![init-gui](https://i.imgur.com/qYZSk3V.png)

Clicking at the zero-point, a dot will appear:
![dot-gui](https://i.imgur.com/3JX51Hr.png)

Closing the GUI, `origin` will now be a set variable. We will use this variable to set the origin at the same position everytime we open ImageP with this image.

Setting the origin position can also be done manually through `Actions->Change origin position`.

## Calibrating the pixel size
It is essential to define the pixel size in order to make measurements based upon the picture. Usually you make a calibration measurement or have a defined length within the frame of your picture. Here, we can simply use the fixed interval of 1 cm on the protractor.

It is good practice to use several points to define the pixel size due to the statistical error caused by slight misclicks in the picture.

```Python
xcal = gui('./test.png', origin=origin, color='black')

# Show the calibration in a plot so we can see the deviation:
plt.figure()
# Calculate differences so we can calculate the div-size in pixels
xdiff = [xcal[i+1]-xcal[i] for i in range(len(xcal)-1)]
xdiff_mean = np.mean(xdiff)
plt.plot(xdiff)
plt.plot([0, len(xdiff)-1], np.ones(2)*xdiff_mean, label='mean')
plt.legend()
plt.grid()[:,0]
```

After clicking the points from left to right, we get the following GUI image and plot:

![cal-gui](https://i.imgur.com/w5CXKFS.png)

Which means that there are about 44.1 pixels per 1 cm.

You can clearly see the deviation from the mean. You can imagine this deviation only getting larger when the resolution of the image is gets lower. You could use the standard error and the T95 value to determine the error in the calibration, but that goes beyond the example.

The exact same thing could be done for the y axis.

From this mean, we will now calculate the pixel size:
```Python
div = 1 # cm
xpixel = div/xdiff_mean # cm
```

The value of `xpixel` (and usually also `ypixel`) can then be put into a tuple which can be passed into the gui function under the `calibration` parameter:

```Python
gui('./test.jpg', origin=origin, calibration=(xpixel, ypixel), unit='cm', color='black')
```

Using `ypixel=xpixel` and `unit='cm'` for this example, we get the following GUI:
![dist-gui](https://i.imgur.com/zBDgxUF.png)

Again, the values for xpixel and ypixel can also be inserted in the program under `Actions->Calibrate`.

## Measuring within ImageP

With a point clicked in the origin (here barely visible) we can start measuring things using the statusbar at the bottom of the GUI. The mouse is at the 5 cm mark, which can also be read under `distance`.

Clicking on point more (at the 5 cm mark), we can also start measuring angles between points:

![ang-gui](https://i.imgur.com/LVWTsuh.png)

Here, as expected, we see an angle of 90 degrees between the point at the 5 cm mark and the point at the 90 degrees mark compared to the origin. To measure the angle correctly, remember that you first click the point in which you want to measure the angle, then the first point and then the cursor gives the angle in the corner of those two lines (see picture above).

## Returned data
After calibrating the pixel size and setting the origin, you may use ImageP for whatever your experiment is about. The `gui` function returns the calibrated points relative to the origin automatically.

## Additional info
If you clicked wrong, you can use `z` to remove the previously clicked dot.

In a more recent version, you will find an extra GUI-element on the right of the window with which you can alter the RGB-levels (or grayscale levels) for better visibility of that what you are clicking.

Happy coding!
