import matplotlib.pyplot as plt
import matplotlib.image as img
import numpy as np

def rgb2gray(rgb):
    r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray

class ImageP:
    def __init__(self, image, plotting, finished):
        self.fig, self.ax = plt.subplots()
        self.ax.imshow(image, cmap='gray')
        self.ax.set_title('Right-click to choose points, close to proceed\nSelect point and hit delete to remove point\nLeft-click to unselect')
        self.points = []
        self.fig.canvas.mpl_connect('button_press_event', self.press)
        self.fig.canvas.mpl_connect('button_release_event', self.release)
        self.fig.canvas.mpl_connect('close_event', self.close)
        self.fig.canvas.mpl_connect('pick_event', self.pick)
        self.fig.canvas.mpl_connect('key_press_event', self.key)
        self.ax.picked_object = None
        self._x = None
        self._y = None
        self.finished = finished
        plotting(self.ax)
        plt.show()

    def press(self, event):
        # we do not know the coordinates when clicking on the border
        # only allow selection when right clicking
        if event.xdata == None or event.ydata == None or event.button.value != 1:
            return

        self._x = event.xdata
        self._y = event.ydata

    def release(self, event):
        # unselecting mechanism
        if event.button.value == 3 and self.ax.picked_object != None:
            self.ax.picked_object.set_color('royalblue')
            self.ax.picked_object = None
            self.ax.figure.canvas.draw()
            return

        # only look for right-click release
        if event.button.value != 1:
            return

        # if we have a selected dot, do not add a new one
        if self.ax.picked_object != None:
            return

        # if the click was a click-and-drag, do not append
        # it might be a pan zoom or move around plot
        if event.xdata == self._x and event.ydata == self._y:
            self.points.append((event.xdata,event.ydata))
            self.ax.scatter(event.xdata, event.ydata, color='royalblue', marker='o', picker=True, pickradius=5)
            self.fig.canvas.draw_idle()

    def close(self, event):
        self.finished(self.points)

    def pick(self, event):
        artist = event.artist
        artist.set_color('red')
        self.ax.picked_object = artist
        self.ax.figure.canvas.draw()

    def key(self, event):
        if event.key != u'delete':
            return
        if self.ax.picked_object != None:
            data = self.ax.picked_object.get_offsets()
            self.points.remove((data[0][0], data[0][1]))
            self.ax.picked_object.remove()
            self.ax.picked_object = None
            self.ax.figure.canvas.draw()
