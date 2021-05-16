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

from PyQt5 import QtWidgets, QtGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import numpy as np
import sys, cv2, warnings
warnings.filterwarnings("error")

VERSION_INFO = 'version 2.1'
CHANGELOG = """Changelog:
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
DOCUMENTATION = """Please view the documentation on the <a href="https://github.com/JitseB/ImageP/blob/main/DOCUMENATION.md">GitHub repository</a>."""

class PlotWidget(QtWidgets.QWidget):
    """Qt widget to hold the matplotlib canvas and the tools for interacting with the plot"""
    def __init__(self, window):
        QtWidgets.QWidget.__init__(self)

        self.setLayout(QtWidgets.QVBoxLayout())
        self.canvas = PlotCanvas(window)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.addSeparator()

        self.toolbar.addSeparator()
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)

class PlotCanvas(FigureCanvas):
    """Class to hold a canvas with a matplotlib figure with the image matrix and origin lines"""
    def __init__(self, window):
        self.window = window

        # setup the FigureCanvas
        self.fig = plt.Figure()
        self.fig.set_tight_layout({"pad": 0.0}) # Remove the axes
        FigureCanvas.__init__(self, self.fig)
        FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.ax = self.fig.subplots()
        self.ax.set_axis_off()
        self.ax.imshow(window.image)
        self.originvline = self.ax.axvline(self.window.origin[0], ls='--', color=self.window.color)
        self.originhline = self.ax.axhline(self.window.origin[1], ls='--', color=self.window.color)

        self.mouse = (0, 0)

        # Connect to all necessary events
        self.connect()

    def redraw(self):
        """Redraw the canvas"""
        self.fig.canvas.draw()

    def connect(self):
        """Connect to all necessary Matplotlib events"""
        self.cidpress = self.fig.canvas.mpl_connect('button_press_event', self._on_click)
        self.cidmotion = self.fig.canvas.mpl_connect('motion_notify_event', self._on_motion)

    def disconnect(self):
        """Disconnect from all used Matplotlib events"""
        self.fig.canvas.mpl_disconnect(self.cidpress)
        self.fig.canvas.mpl_disconnect(self.cidmotion)
        
    def get_cursor(self):
        """Get the coordinates of the cursor"""
        return self.cursor

    def _on_click(self, event):
        """Internal function to handle the Matplotlib click event, used to click points and set the origin position"""
        if not event.xdata or not event.ydata: return

        # If the origin was moving, lock it in place
        if self.window.move_origin:
            self.window.move_origin = False
            self.window.origin = self.get_cursor()
            return

        # if there is a right-click, add the coords to the points array
        if event.button.value == 1:
            self.window.points.append(self.get_cursor())
            self.ax.scatter(event.xdata, event.ydata, marker='.', color=self.window.color)
            self.redraw()

    def _on_motion(self, event):
        """Internal function to handle the Matplotlib motion event, used to track the cursor for the origin lines and statusbar"""
        if not event.xdata or not event.ydata: return

        # If the origin is movable, move the lines with the cursor
        if self.window.move_origin:
            self.originvline.set_xdata(event.xdata)
            self.originhline.set_ydata(event.ydata)
            self.redraw()

        # Set the mouse coordinates and update the statusbar
        self.cursor = (event.xdata, event.ydata)
        self.window._update_statusbar()

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
        except Exception:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText('An error occurred!')
            msg.setInformativeText('Numbers entered were invalid.')
            msg.setWindowTitle('ImageP Error')
            msg.exec_()

class ImageWindow(QtWidgets.QMainWindow):
    def __init__(self, image, origin, calibration, unit, color):
        super(ImageWindow, self).__init__()
        self.image = image
        self.origin = origin
        self.calibration = calibration
        self.unit = unit # Default unit is pixels
        self.points = []
        self.color = color
        self.move_origin = False
        self._init_gui()

    def closeEvent(self, event):
        # Needed to properly quit when running in IPython console / Spyder IDE
        QtWidgets.QApplication.quit()

    def _init_gui(self):
        """Internal function that creates the GUI"""
        self.setGeometry(100, 100, 900, 650)
        self.setWindowTitle('ImageP ' + VERSION_INFO)
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)

        # Put plot in main layout
        layout = QtWidgets.QVBoxLayout(self._main)
        self.plotwidget = PlotWidget(self)
        layout.addWidget(self.plotwidget)

        # Add menu items
        actionsMenu = self.menuBar().addMenu("&Actions")
        calibrate_action = QtWidgets.QAction("&Calibrate", self)
        actionsMenu.addAction(calibrate_action)
        calibrate_action.triggered.connect(self._show_calibration_dialog)
        origin_action = QtWidgets.QAction("&Change origin position", self)
        actionsMenu.addAction(origin_action)
        origin_action.triggered.connect(self._enable_moving_origin)
        helpMenu = self.menuBar().addMenu("&Help")
        help_action = QtWidgets.QAction("&Documentation", self)
        helpMenu.addAction(help_action)
        help_action.triggered.connect(self._show_documentation_popup)
        about_action = QtWidgets.QAction("&About and credits", self)
        helpMenu.addAction(about_action)
        about_action.triggered.connect(self._show_about_popup)

        # Add status bar items
        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)
        self.mouse_position_label = QtWidgets.QLabel(f'Position: -')
        self.statusBar.addWidget(self.mouse_position_label)
        self.dist_label = QtWidgets.QLabel('Distance: -')
        self.statusBar.addWidget(self.dist_label)
        self.angle_label = QtWidgets.QLabel('Angle: -')
        self.statusBar.addWidget(self.angle_label)

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

        msg.setText('ImageP is a minimalistic Python version of <a href="https://imagej.nih.gov/ij/">ImageJ</a> written by and for Applied Physics students at the University of Twente. It is licensed under the MIT license.<br><br>ImageP uses <a href="https://www.riverbankcomputing.com/software/pyqt/">PyQt</a> for the GUI and <a href="https://opencv.org//">OpenCV</a> together with <a href="https://numpy.org/">NumPy</a> for file loading.<br><br>View <a href="https://github.com/JitseB/ImageP">GitHub repository</a> for updates.')
        msg.setInformativeText(CHANGELOG)
        msg.setWindowTitle('ImageP About and credits')
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
        self.move_origin = True

    def _update_statusbar(self):
        """Internal function to update the statusbar labels"""
        # All points (A, B and C) are measured from the origin position
        # Using cosine rule to solve angle (finding angle(CAB), so between the lines AC and AB)
        C = self.get_relative_calibrated(self.plotwidget.canvas.get_cursor())
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
                except RuntimeWarning:
                    pass # Do not do anything, it is most likely a devide by zero error

def gui(path, origin=None, calibration=(1, 1), unit='px', color='black'):
    """
    Function that opens the GUI of ImageP. Returns array with calibrated clicked points relative to the origin.
    Parameters:
        - 'image_path': Path to image.
        - 'origin': Change the origin to position xy (optional).
            If the passed origin is not in pixel units, you must pass 'pixel_origin'=False,
            so that the origin position is calculated correctly from the entered unit size.
            By default 'pixel_origin' is True.
        - 'calibration': The pixel calibration array (x and y pixel size) (optional).
        - 'color': The color used for the axis and points (optional).

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
        window.show()
        app.exec_()
        
        # Return the calibrated points
        return window.get_calibrated_points()
    except Exception as e:
        raise e
        # If it is not an image, try to load the video
        print('Video files are not supported yet!')
        # cap = cv2.VideoCapture(path)
        # if not cap.isOpened(): raise FileNotFoundError
        # app = QtWidgets.QApplication([])
        # window = VideoWindow(cap, origin, calibration, color)
        # window.show()
        # app.exec_()
        # TODO: Return the calibrated points

# Test the application with a test image
if __name__ == '__main__':
    print(gui('./test.png', color='white'))
