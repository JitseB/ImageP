# MIT License

# Copyright (c) 2021 Jitse Boonstra

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from PyQt5 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg
import numpy as np
import sys, cv2, warnings
warnings.filterwarnings("error")

VERSION_INFO = 'version 2.5'
CHANGELOG = """Changelog:
Version 2.5 (19 June 2021):
    - Swapped out Matplotlib for PyQtGraph for better video performance.
    - Added LUT (lookup-table) to change different levels of red-green-blue.
    - Added image/frame grayscale converter as tickbox in the GUI.
Version 2.4 (26 May 2021):
    - Refactoring.
    - Bug fix: When setting the 'frame' parameter, the initial frame now corresponds to this value.
Version 2.3 (25 May 2021):
    - Bug fix: When no dots have been clicked yet, the menu ctrl+z button no longer throws an error.
    - Video files are now supported! By using the right and left arrow one can flip through the frames.
    - Auto-progress parameter was added for videos.
    - Added frame number to statusbar for videos.
    - Added alpha parameters (also: keep_alpha parameter) to change axis and dot opacity.
    - Added 'auto_progress_frame_interval' as video parameter so that frames can be skipped when auto-progressing the frames.
Version 2.2 (22 May 2021):
    - Bug fix: No dot added when in zoom or pan mode.
    - Added ctrl+z feature to remove previously clicked dot.
Version 2.1 (16 May 2021):
    - Bug fix: 'gui'-parameters now actually work.
    - Bug fix: Reuse QtApplication, otherwise the kernel dies in Jupyter notebooks.
    - Bug fix: Catching warning caused by angle measurement.
    - Removed unit origin as we cannot know it previous position, therefore we cannot compensate for it properly.
Version 2.0 (16 May 2021):
    - Converted to PyQt5 application for more functionality.
    - Added movable origin and button.
    - Added About and Help page.
    - Changed Pillow out for OpenCV for future compatibility of videos.
    - Added status bar with position, distance and angle texts.
    - Added pixel calibration mechanism.
    - Lots of refactoring and added documentation.
Version 1.0 (9 May 2021):
    - Simple single class image processor using a Matplotlib GUI and its events.
"""
DOCUMENTATION = """Please view the documentation on the <a href="https://github.com/JitseB/ImageP/blob/main/DOCUMENTATION.md">GitHub repository</a>."""

class PlotWidget(QtWidgets.QWidget):
    point_add_event = QtCore.pyqtSignal(tuple)
    point_remove_last_event = QtCore.pyqtSignal()
    origin_change_event = QtCore.pyqtSignal(tuple)
    mouse_move_event = QtCore.pyqtSignal(tuple)
    
    """Qt widget to hold the PyQtGraph widget and the tools for interacting with the plot"""
    def __init__(self, window):
        QtWidgets.QWidget.__init__(self)
        self.image = np.flipud(np.rot90(window.image))
        self.color = window.color
        self._shift_active = False
        self.origin_move_active = False
        self._grayscale_active = False
        
        self.canvas = pg.ImageView()

        # Use a grid layout for the plot, LUT and settings (with title)
        # Since the settings and LUT only need local referencing, we do not have to create a seperate class
        layout = QtGui.QGridLayout()
        self.setLayout(layout)

        self.lut = pg.HistogramLUTWidget()
        layout.addWidget(self.lut, 1, 1)

        self._plt = pg.plot()
        self._plt.setAspectLocked(True)

        self.img = pg.ImageItem(self.image)
        self.img.setZValue(-10)

        self.scatter = pg.ScatterPlotItem(pen=None, brush=pg.mkBrush(self.color))
        self._plt.addItem(self.scatter)

        self._plt.addItem(self.img)
        self._plt.invertY(True) # Vertical axis counts top to bottom
        self._plt.hideAxis('left')
        self._plt.hideAxis('bottom')
        layout.addWidget(self._plt, 0, 0, 5, 1)

        self.lut.setImageItem(self.img)
        
        # Settings (with title)
        label = QtGui.QLabel('Image post-processing')
        label.setStyleSheet("font-weight:bold;text-align:center")
        layout.addWidget(label, 0, 1)
        grayBox = QtGui.QCheckBox('grayscale')
        monoRadio = QtGui.QRadioButton('mono')
        rgbaRadio = QtGui.QRadioButton('rgba')
        grayBox = QtGui.QCheckBox('grayscale')
        layout.addWidget(monoRadio, 2, 1)
        layout.addWidget(rgbaRadio, 3, 1)
        layout.addWidget(grayBox, 4, 1)
        monoRadio.setChecked(True)

        # Grayscale click action
        def setGrayscale(state):
            if state == QtCore.Qt.Checked:
                # Convert rgb image to gray image using std formula
                self.img.setImage(np.dot(self.image[...,:3], [0.299, 0.587, 0.114]))
                monoRadio.setChecked(True)
                rgbaRadio.setChecked(False)
                rgbaRadio.setEnabled(False)
                self._grayscale_active = True
            else:
                self.img.setImage(self.image)
                rgbaRadio.setEnabled(True)
                self._grayscale_active = False
        
        # Connect state change events to their functions
        grayBox.stateChanged.connect(setGrayscale)
        monoRadio.toggled.connect(lambda _: self.lut.setLevelMode('mono' if monoRadio.isChecked() else 'rgba'))

        # Disable the grayscale and rgb buttons if the image dooes not have rgb data
        if len(self.image.shape) < 3: 
            grayBox.setEnabled(False)
            rgbaRadio.setEnabled(False)

        # Origin lines
        self._origin_vline = pg.InfiniteLine(angle=90, pos=window.origin[0], pen=self.color, movable=False)
        self._origin_hline = pg.InfiniteLine(angle=0, pos=window.origin[1], pen=self.color, movable=False)
        self._plt.addItem(self._origin_vline, ignoreBounds=True)
        self._plt.addItem(self._origin_hline, ignoreBounds=True)

        # Connect the signal proxies and events
        self._mouse_move_proxy = pg.SignalProxy(self._plt.scene().sigMouseMoved, rateLimit=60, slot=self._mouse_move_handler)
        self._mouse_click_proxy = pg.SignalProxy(self._plt.scene().sigMouseClicked, rateLimit=60, slot=self._mouse_click_handler)
        window.key_press_event.connect(self._key_press_handler)
        window.key_release_event.connect(self._key_release_handler)

    # Event handlers
    def _key_press_handler(self, key):
        if key == QtCore.Qt.Key_Shift: self._shift_active = True
        elif key == QtCore.Qt.Key_Z: self.point_remove_last_event.emit()
        
    def _key_release_handler(self, key):
        if key == QtCore.Qt.Key_Shift: self._shift_active = False

    def _mouse_move_handler(self, event):
        pos = event[0] # Using signal proxy turns original arguments into a tuple
        if self._plt.sceneBoundingRect().contains(pos):
            mouse_position = self._plt.plotItem.vb.mapSceneToView(pos)
            self.mouse_move_event.emit((mouse_position.x(), mouse_position.y()))

            if self.origin_move_active:
                self._origin_hline.setPos(mouse_position.y())
                self._origin_vline.setPos(mouse_position.x())
                self.origin_change_event.emit((mouse_position.x(), mouse_position.y()))

    def _mouse_click_handler(self, event):
        if event[0] == None: return # Prevent attribute error
        pos = event[0].pos() # Using signal proxy turns original arguments into a tuple
        if self.origin_move_active:
            self.origin_move_active = False
            return

        if self._shift_active: self.point_add_event.emit((pos.x(), pos.y()))

    def update_points(self, points):
        """Update the scatter plot with the points"""
        self.scatter.setData(pos=points)

    # Plot widget functions
    def set_origin(self, position):
        """Change the origin's position to a new location"""
        self.origin = position
        self.origin_hline.setPos(position[0])
        self._origin_vline.setPos(position[1])

    def set_image(self, image):
        """Change the current image that is shown"""
        self.image = np.flipud(np.rot90(image))
        # Set image on the view and copy over the levels (LUT)
        levels = self.lut.getLevels()
        self.img.setImage(self.image if not self._grayscale_active else np.dot(self.image[...,:3], [0.299, 0.587, 0.114]))
        if self.lut.levelMode == 'mono': self.lut.setLevels(min=levels[0], max=levels[1])
        else: self.lut.setLevels(rgba=levels)
        self.lut.regionChanged() # Tell PyQtGrapg the LUT regions have changed to update the image view

class CalibrationDialog(QtWidgets.QDialog):
    """Qt dialog class for the calibration popup"""
    def __init__(self):
        super().__init__()

        # Create the window and add all form elements
        self.setWindowTitle('ImageP Calibration')

        buttons = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self._onaccept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QtWidgets.QFormLayout()
        self.layout.addRow(QtWidgets.QLabel('Enter the size of each pixel and provide a unit'))
        self.xedit = QtWidgets.QLineEdit()
        self.xedit.setValidator(QtGui.QDoubleValidator())
        self.layout.addRow('X-direction pixel size', self.xedit)
        self.yedit = QtWidgets.QLineEdit()
        self.yedit.setValidator(QtGui.QDoubleValidator())
        self.layout.addRow('Y-direction pixel size', self.yedit)
        self.unitedit = QtWidgets.QLineEdit()
        self.layout.addRow('Unit', self.unitedit)
        self.layout.addRow(self.buttonBox)
        self.setLayout(self.layout)

    def get_xy_calibration(self):
        """Convert the entered calibration values to floats and return them as a tuple"""
        return (float(self.xedit.text()), float(self.yedit.text()))

    def get_unit(self):
        """Get the entered unit"""
        return self.unitedit.text()

    def _onaccept(self):
        """
        This internal function adds a bit of functionality to the self.accept function, it
        checks whether the entered values are numbers. If not, an error dialog will show.
        """
        try:
            self.get_xy_calibration()
            self.accept()
        except Exception as e:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText('An error occurred!')
            msg.setInformativeText('Numbers entered were invalid.')
            msg.setWindowTitle('ImageP Error')
            msg.exec_()

class ImageWindow(QtWidgets.QMainWindow):
    key_press_event = QtCore.pyqtSignal(int)
    key_release_event = QtCore.pyqtSignal(int)

    """Class for the image window of ImageP"""
    def __init__(self, image, origin, calibration, unit, color):
        super(ImageWindow, self).__init__()
        self.image = image
        self.origin = origin
        self.calibration = calibration
        self.unit = unit # Default unit is pixels
        self.color = color
        self.points = []

    def closeEvent(self, event):
        # Needed to properly quit when running in IPython console / Spyder IDE
        QtWidgets.QApplication.quit()

    def keyPressEvent(self, event):
        """Event for key press"""
        self.key_press_event.emit(event.key())

    def keyReleaseEvent(self, event):
        """Event for key release"""
        self.key_release_event.emit(event.key())

    def init_gui(self):
        """Internal function that creates the GUI"""
        self.setGeometry(100, 100, 900, 650)
        self.setWindowTitle('ImageP ' + VERSION_INFO)
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)

        # Put plot in main layout
        layout = QtWidgets.QVBoxLayout(self._main)
        self.plotwidget = PlotWidget(self)

        self.plotwidget.point_remove_last_event.connect(self.point_remove_last_listener)
        self.plotwidget.point_add_event.connect(self.point_add_listener)
        self.plotwidget.mouse_move_event.connect(self._update_statusbar_handler)
        self.plotwidget.origin_change_event.connect(self._origin_change_listener)

        layout.addWidget(self.plotwidget)

        # Add menu items
        def _add_action(menu, text, function):
            """Small internal function to add an action to a menu with a certain trigger function"""
            # Solely made to clean up the codebase
            action = QtWidgets.QAction(text, self)
            menu.addAction(action)
            action.triggered.connect(function)

        actions = self.menuBar().addMenu('&Actions')
        _add_action(actions, '&Calibrate', self._show_calibration_dialog)
        _add_action(actions, '&Move origin', self._enable_moving_origin)

        help = self.menuBar().addMenu('&Help')
        _add_action(help, '&Documentation', self._show_documentation_popup)
        _add_action(help, '&Keyboard shortcuts', self._show_keymap_popup)
        _add_action(help, '&About and credits', self._show_about_popup)

        # Add status bar items
        self.statusbar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusbar)

        self.mouse_position_label = QtWidgets.QLabel(f'Position: -')
        self.statusbar.addWidget(self.mouse_position_label)
        self.dist_label = QtWidgets.QLabel('Distance: -')
        self.statusbar.addWidget(self.dist_label)
        self.angle_label = QtWidgets.QLabel('Angle: -')
        self.statusbar.addWidget(self.angle_label)

    def point_remove_last_listener(self):
        """Remove that last clicked point (operated with z-key)"""
        if len(self.points) > 0: 
            self.points = self.points[:-1]
            self.plotwidget.update_points(self.points)

    def point_add_listener(self, point):
        """When a point is clicked, add it to the list and update the scatter plot"""
        self.points.append(point)
        self.plotwidget.update_points(self.points)

    def get_relative_calibrated(self, point):
        """Get point position relative to origin and apply calibration"""
        # First position the points relative to the origin, then multiply by their calibration factors
        return ((point[0]-self.origin[0])*self.calibration[0], ((self.origin[1]-point[1])*self.calibration[1]))

    def get_calibrated_points(self):
        """Returns the array we were after, the calibrated points from the image relative to the origin"""
        # Convert to NumPy array for easier matrix manipulation
        return np.array([self.get_relative_calibrated(point) for point in self.points])

    def _show_documentation_popup(self):
        """Internal function to show the documentation popup window"""
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)

        msg.setText(DOCUMENTATION)
        msg.setWindowTitle("ImageP Documentation")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()

    def _show_about_popup(self):
        """Internal function to show the about and credits popup window"""
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)

        msg.setText('ImageP is a minimalistic Python version of <a href="https://imagej.nih.gov/ij/">ImageJ</a> written by and for Applied Physics students at the University of Twente. It is licensed under the MIT license.<br><br>ImageP uses <a href="https://www.riverbankcomputing.com/software/pyqt/">PyQt</a> for the GUI and <a href="https://opencv.org//">OpenCV</a> together with <a href="https://numpy.org/">NumPy</a> for file loading. <a href="https://www.pyqtgraph.org/">PyQtGraph</a> is used to display the data.<br><br>View <a href="https://github.com/JitseB/ImageP">GitHub repository</a> for updates.')
        msg.setInformativeText(CHANGELOG)
        msg.setWindowTitle('ImageP About and credits')
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()

    def _show_keymap_popup(self):
        """Internal function to show the keymap window"""
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)

        msg.setText('Keyboard shortcuts')
        msg.setInformativeText('Press z to remove the previously clicked dot.\nUse the arrow keys to move through the frames of a video file.')
        msg.setWindowTitle('ImageP Keymap')
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()

    def _show_calibration_dialog(self):
        """Internal function to show the calibration dialog"""
        dialog = CalibrationDialog()
        if not dialog.exec(): return # Dialog was cancelled or closed
        # Set internal variables
        self.calibration = dialog.get_xy_calibration()
        self.unit = dialog.get_unit()

    def _enable_moving_origin(self):
        """Internal function to enable movement of the origin"""
        self.plotwidget.origin_move_active = True

    def _origin_change_listener(self, origin):
        self.origin = origin

    def _update_statusbar_handler(self, mouse_position):
        """Internal function to update the statusbar labels"""
        # All points (A, B and C) are measured from the origin position
        # Using cosine rule to solve angle (finding angle(CAB), so between the lines AC and AB)
        C = self.get_relative_calibrated(mouse_position)
        self.mouse_position_label.setText(f'Position: x={C[0]:.2f} {self.unit}; y={C[1]:.2f} {self.unit}')
        if len(self.points) >= 1:
            B = self.get_relative_calibrated(self.points[-1])
            distanceBC = ((B[0]-C[0])**2+(B[1]-C[1])**2)**(1/2)
            self.dist_label.setText(f'Distance: {distanceBC:.2f} {self.unit}')
            if len(self.points) >= 2:
                A = self.get_relative_calibrated(self.points[-2])
                distanceAC = ((A[0]-C[0])**2+(A[1]-C[1])**2)**(1/2)
                distanceAB = ((A[0]-B[0])**2+(A[1]-B[1])**2)**(1/2)
                try:
                    angle = np.arccos((distanceAC**2+distanceAB**2-distanceBC**2)/(2*distanceAC*distanceAB))*180/np.pi
                    self.angle_label.setText(f'Angle: {angle:.2f} deg')
                except RuntimeWarning as w: pass
                except ZeroDivisionError as e: pass

class VideoWindow(ImageWindow):
    """Class for the video window of ImageP"""
    def __init__(self, capture, origin, calibration, unit, color, frame, auto_progress, auto_progress_frame_interval):
        self.capture = capture
        self.frame = frame
        self.auto_progress = auto_progress
        self.auto_progress_frame_interval = auto_progress_frame_interval
        self.max_frame = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))-1
        self.capture.set(1, frame) # Set the frame number within the VideoCapture object
        success, image = self.capture.read()
        if not success: raise Exception('Could not read video capture')
        # Convert image data to RGB for Matplotlib
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # The origin point was returned calibrated from the (0, 0) origin, we have to compensate for that...
        if origin is not None: origin = (origin[0], image.shape[0]-origin[1]) 
        else: origin = (0, image.shape[0])

        super(VideoWindow, self).__init__(image, origin, calibration, unit, color)

    def init_video_gui(self):
        """Initialize the video GUI"""
        # First initialize the image GUI, then add to that:
        self.init_gui()

        # Connect to the necessary events
        self.key_press_event.connect(self._key_press_listener)
        self.plotwidget.point_add_event.connect(self._auto_progress_handler)
        self.plotwidget.point_remove_last_event.connect(self._point_remove_last_listener)

        # Add an extra label for the frame number to the status bar
        self.frame_label = QtWidgets.QLabel(f'Frame: {self.frame}/{self.max_frame}')
        self.statusbar.addWidget(self.frame_label)

    def _key_press_listener(self, key):
        """Listener for key press event so that the user can move through the frames"""
        if key == QtCore.Qt.Key_Right and self.frame < self.max_frame: self._change_frame(self.frame+1)
        elif key == QtCore.Qt.Key_Left and self.frame > 0:  self._change_frame(self.frame-1)

    def _point_remove_last_listener(self):
        """Additional listener (see image class) so that when auto progressing, using the z-key, it goes back in time"""
        # Roll back the frames when auto-progressing is enabled
        if self.auto_progress: self._change_frame(self.frame - self.auto_progress_frame_interval)

    def _change_frame(self, frame):
        """Internal function to change the frame currently visible"""
        self.capture.set(1, frame) # Set the frame number within the VideoCapture object
        success, image = self.capture.read()
        if not success: return False
        # Convert image data to RGB for Matplotlib
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.plotwidget.set_image(image)

        # Set frame label to correct frame number
        self.frame_label.setText(f'Frame: {frame}/{self.max_frame}')
        self.frame = frame
        return True

    def _auto_progress_handler(self, _):
        """Internal function as listener for the button click event from PyQtGraph, only triggers when a point is placed"""
        # If 'auto_progress' is true, move to next frame
        if self.auto_progress and not self._change_frame(self.frame + self.auto_progress_frame_interval): 
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText('Cannot move any further!')
            msg.setInformativeText('You ran out of frames to click.')
            msg.setWindowTitle('ImageP Error')
            msg.exec_()

def gui(path, origin=None, calibration=(1, 1), unit='px', color='w', frame=0, auto_progress=False, auto_progress_frame_interval=10):
    """
    Function that opens the GUI of ImageP. Returns array with calibrated clicked points relative to the origin.
    Parameters:
        - 'path': Path to image or video.
        - 'origin': Change the origin to position xy (optional) (always in pixels!).
        - 'calibration': The pixel calibration array (x and y pixel size) (optional).
        - 'unit': The unit caused by the calibration array (pixels [px] by default).
            If an array with the calibration values for the pixels was passed, it is recommended to also pass the corresponding unit to prevent confusion later on.
        - 'color': The color used for the axis and points (optional) (white by default).
        VIDEO ONLY:
        - 'frame': The frame to start the program from (0 by default).
        - 'auto_progress': Automatically progress to the next frame after clicking (false by default).
        - 'auto_progress_frame_interval': Frames that are skipped when auto-progressing (10 frames per click by default).

    'origin', 'calibration' and 'unit' can also be defined from within the GUI.
   """

    try:
        # Load the image
        image = cv2.imread(path)
        if image is None: raise Exception
        # Convert image data to RGB for Matplotlib
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # The origin point was returned calibrated from the (0, 0) origin, we have to compensate for that...
        # 16 May 2021:  Removed unit origin as we cannot know the previous origin, therefore we cannot
        #               compensate for it properly.
        if origin is not None: origin = (origin[0], image.shape[0]-origin[1]) 
        else: origin = (0, image.shape[0])

        # Launch the GUI application
        # Use previous instance if available
        if not QtWidgets.QApplication.instance(): app = QtWidgets.QApplication(sys.argv)
        else: app = QtWidgets.QApplication.instance()
        window = ImageWindow(image, origin, calibration, unit, color)
        window.init_gui()
        window.show()
        app.exec_()
        
        # Return the calibrated points
        return window.get_calibrated_points()
    except Exception as e:
        # If it is not an image, try to load the video
        capture = cv2.VideoCapture(path)
        if not capture.isOpened(): raise FileNotFoundError('The specified file could not be found (or loaded)')
        # Launch the GUI application
        # Use previous instance if available
        if not QtWidgets.QApplication.instance(): app = QtWidgets.QApplication(sys.argv)
        else: app = QtWidgets.QApplication.instance()
        window = VideoWindow(capture, origin, calibration, unit, color, frame, auto_progress, auto_progress_frame_interval)
        window.init_video_gui()
        window.show()
        app.exec_()
        
        # Return the calibrated points
        return window.get_calibrated_points()

# Test the application with a test image
if __name__ == '__main__':
    points = gui('./test.avi', color='w', frame=2000, auto_progress=True, auto_progress_frame_interval=10)
    print(points)
