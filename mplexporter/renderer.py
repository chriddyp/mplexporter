"""
Matplotlib Renderer
===================
This submodule contains renderer objects which define renderer behavior used
within the Exporter class.
"""
import warnings
from contextlib import contextmanager


class Renderer(object):
    @staticmethod
    def ax_zoomable(ax):
        return bool(ax and ax.get_navigate())

    @staticmethod
    def ax_has_xgrid(ax):
        return bool(ax and ax.xaxis._gridOnMajor and ax.yaxis.get_gridlines())

    @staticmethod
    def ax_has_ygrid(ax):
        return bool(ax and ax.yaxis._gridOnMajor and ax.yaxis.get_gridlines())

    @property
    def current_ax_zoomable(self):
        return self.ax_zoomable(self._current_ax)

    @property
    def current_ax_has_xgrid(self):
        return self.ax_has_xgrid(self._current_ax)

    @property
    def current_ax_has_ygrid(self):
        return self.ax_has_ygrid(self._current_ax)

    @contextmanager
    def draw_figure(self, fig):
        if hasattr(self, "_current_fig") and self._current_fig is not None:
            warnings.warn("figure embedded in figure: something is wrong")
        self._current_fig = fig
        self.open_figure(fig)
        yield
        self.close_figure(fig)
        self._current_fig = None

    @contextmanager
    def draw_axes(self, ax):
        if hasattr(self, "_current_ax") and self._current_ax is not None:
            warnings.warn("axes embedded in axes: something is wrong")
        self._current_ax = ax
        self.open_axes(ax)
        yield
        self.close_axes(ax)
        self._current_ax = None

    # Following are the functions which should be overloaded in subclasses

    def open_figure(self, fig):
        pass

    def close_figure(self, fig):
        pass

    def open_axes(self, ax):
        pass

    def close_axes(self, ax):
        pass

    def draw_line(self, data, coordinates, style):
        raise NotImplementedError()

    def draw_markers(self, data, coordinates, style):
        raise NotImplementedError()
