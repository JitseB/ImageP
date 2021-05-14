from PyQt5 import QtCore, QtWidgets, QtGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import matplotlib.pyplot as plt

import numpy as np
from PIL import Image

VERSION_INFO = 'ImageP version 2.0'
CHANGELOG = """Changelog:
Version 2.0 (14 May 2021):
    - Converted to PyQt5 application for more functionality.
    - Added movable origin and button.
    - Added About and Help page.
Version 1.0 (9 May 2021):
    - Simple single class image processor using a Matplotlib GUI and its events.
"""
HELP = """ImageP uses Pillow
"""

class PlotWidget(QtWidgets.QWidget):
    """ Qt widget to hold the matplotlib canvas and the tools for interacting with the plots """
    def __init__(self, window):
        QtWidgets.QWidget.__init__(self)

        self.setLayout(QtWidgets.QVBoxLayout())
        self.canvas = PlotCanvas(window)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.addSeparator()

        self.toolbar.addSeparator()
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)

    def get_mouse_position(self):
        return (self.canvas.mouse[0]-self.canvas.origin[0], self.canvas.origin[1]-self.canvas.mouse[1])


class PlotCanvas(FigureCanvas):
    """ class to hold a canvas with a matplotlib figure and two subplots for plotting data and residuals """
    def __init__(self, window):
        self.window = window
        # setup the FigureCanvas
        self.fig = plt.Figure()
        self.fig.set_tight_layout({"pad": 0.0})
        FigureCanvas.__init__(self, self.fig)
        FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.ax = self.fig.subplots()
        self.ax.set_axis_off()
        self.ax.imshow(window.image)
        self.originvline = self.ax.axvline(self.window.origin[0], ls='--', color=self.window.color)
        self.originhline = self.ax.axhline(self.window.origin[1], ls='--', color=self.window.color)

        self.mouse = (0, 0)
        self.origin = (0, 0)

        # Connect to all necessary events
        self.connect()

    def redraw(self):
        self.fig.canvas.draw()

    def connect(self):
        self.ciddraw = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        self.ciddraw = self.fig.canvas.mpl_connect('motion_notify_event', self.onmotion)

    def onclick(self, event):
        if not event.xdata or not event.ydata: return

        # If the origin was moving, lock it in place
        if self.window.move_origin:
            self.window.move_origin = False
            self.origin = self.mouse
            return

        # if there is a right-click, add the coords to the points array
        if event.button.value == 1:
            self.window.points.append((self.mouse[0]-self.origin[0], self.origin[1]-self.mouse[1]))
            self.ax.scatter(event.xdata, event.ydata, marker='.', color=self.window.color)
            self.redraw()

    def onmotion(self, event):
        if not event.xdata or not event.ydata: return

        if self.window.move_origin:
            self.originvline.set_xdata(event.xdata)
            self.originhline.set_ydata(event.ydata)
            self.redraw()

        self.mouse = (event.xdata, event.ydata)
        self.window.update_mouse_position()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, image, origin, calibration, color):
        super(MainWindow, self).__init__()
        self.image = image
        self.origin = origin
        self.calibration = calibration
        self.points = []
        self.color = color
        self.move_origin = False
        self.init_gui()

    def closeEvent(self, event):
        """needed to properly quit when running in IPython console / Spyder IDE"""
        QtWidgets.QApplication.quit()

    def init_gui(self):
        self.setGeometry(100, 100, 900, 650)
        self.setWindowTitle(VERSION_INFO)
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)

        self.plotwidget = PlotWidget(self)

        box = QtWidgets.QVBoxLayout(self._main)

        menu = self.menuBar().addMenu("&Menu")
        help_action = QtWidgets.QAction("&Help contents", self)
        menu.addAction(help_action)
        help_action.triggered.connect(self.help_clicked)
        about_action = QtWidgets.QAction("&About and credits", self)
        menu.addAction(about_action)
        about_action.triggered.connect(self.about_clicked)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter.addWidget(self.plotwidget)

        frame = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        position = self.plotwidget.get_mouse_position()
        frame2 = QtWidgets.QWidget()
        position_layout = QtWidgets.QVBoxLayout()
        frame2.setLayout(position_layout)
        self.mouse_position_label = QtWidgets.QLabel(f'Mouse position: x={position[0]:.2f}, y={position[1]:.2f} (from origin)')
        self.mouse_position_label.setWordWrap(True)
        position_layout.addWidget(self.mouse_position_label)
        position_layout.addWidget(QtWidgets.QPushButton('Move origin position', clicked=self.move_origin_button))
        layout.addWidget(frame2)

        label2 = QtWidgets.QLabel('Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.')
        label2.setWordWrap(True)
        layout.addWidget(label2)
        frame.setLayout(layout)

        splitter.addWidget(frame)
        box.addWidget(splitter)

    def help_clicked(self):
       msg = QtWidgets.QMessageBox()
       msg.setIcon(QtWidgets.QMessageBox.Information)

       msg.setText("Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.")
       msg.setInformativeText(HELP)
       msg.setWindowTitle("ImageP Help")
       msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
       msg.exec_()

    def about_clicked(self):
       msg = QtWidgets.QMessageBox()
       msg.setIcon(QtWidgets.QMessageBox.Information)

       msg.setText('ImageP is a minimalistic Python version of <a href="https://imagej.nih.gov/ij/">ImageJ</a> written by and for Applied Physics students at the University of Twente. It is licensed under the MIT license.<br><br>ImageP uses <a href="https://www.riverbankcomputing.com/software/pyqt/">PyQt</a> for the GUI and <a href="https://python-pillow.org/">Pillow</a> together with <a href="https://numpy.org/">NumPy</a> for image loading.<br><br>View <a href="https://github.com/JitseB/ImageP">GitHub repository</a> for updates.')
       msg.setInformativeText(CHANGELOG)
       msg.setWindowTitle('ImageP About and credits')
       msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
       msg.exec_()

    def move_origin_button(self):
        self.move_origin = True

    def get_calibrated_points(self):
        return [(point[0]*self.calibration[0], point[1]*self.calibration[1]) for point in self.points]

    def update_mouse_position(self):
        position = self.plotwidget.get_mouse_position()
        self.mouse_position_label.setText(f'Mouse position: x={position[0]:.2f}, y={position[1]:.2f} (from origin)')

def gui(image_path, origin=(0, 0), calibration=(1, 1), color='black'):
    """
    Function that opens the GUI of ImageP. Returns array with clicked points.
    Clicked points are multiplied by the calibration array, by default 1 pixel is 1 unit length.
    'image_path' should be a path to the image, by default the image is changed to grayscale.
    (Reason for the grayscale is that sometimes Matplotlib has issues displaying large coloured images).
    """
    #TODO: coordinates: allow for cart and polar, origin should be movable

    image = np.asarray(Image.open(image_path))

    app = QtWidgets.QApplication([])
    window = MainWindow(image, origin, calibration, color)
    window.show()
    app.exec_()
    return window.get_calibrated_points()

# Test the application with a test image
if __name__ == '__main__':
    points = gui('./test.png', color='white')
    print(points)
