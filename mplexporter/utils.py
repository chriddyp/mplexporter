"""
Utility Routines for Working with Matplotlib Objects
====================================================
"""
import itertools
import io
import base64

import numpy as np

import matplotlib
from matplotlib.colors import colorConverter
from matplotlib.path import Path
from matplotlib.markers import MarkerStyle
from matplotlib.transforms import Affine2D
from matplotlib import ticker


def color_to_hex(color):
    """Convert matplotlib color code to hex color code"""
    if color in ['none', 'None', None]:
        return 'none'
    else:
        rgb = colorConverter.to_rgb(color)
        return '#{0:02X}{1:02X}{2:02X}'.format(*(int(255 * c) for c in rgb))


def many_to_one(input_dict):
    """Convert a many-to-one mapping to a one-to-one mapping"""
    return dict((key, val)
                for keys, val in input_dict.items()
                for key in keys)

LINESTYLES = many_to_one({('solid', '-', (None, None)): "10,0",
                          ('dashed', '--'): "6,6",
                          ('dotted', ':'): "2,2",
                          ('dashdot', '-.'): "4,4,2,4",
                          ('', ' ', 'None', 'none'): "none"})


def get_dasharray(obj, i=None):
    """Get an SVG dash array for the given matplotlib linestyle

    Parameters
    ----------
    obj : matplotlib object
        The matplotlib line or path object, which must have a get_linestyle()
        method which returns a valid matplotlib line code
    i : integer (optional)

    Returns
    -------
    dasharray : string
        The HTML/SVG dasharray code associated with the object.
    """
    if obj.__dict__.get('_dashSeq', None) is not None:
        return ','.join(map(str, obj._dashSeq))
    else:
        ls = obj.get_linestyle()
        if i is not None:
            ls = ls[i]

        dasharray = LINESTYLES.get(ls, None)
        if dasharray is None:
            warnings.warn("dash style '{0}' not understood: "
                          "defaulting to solid.".format(ls))
            dasharray = LINESTYLES['-']
        return dasharray


PATH_DICT = {Path.LINETO: 'L',
             Path.MOVETO: 'M',
             Path.CURVE3: 'S',
             Path.CURVE4: 'C',
             Path.CLOSEPOLY: 'Z'}


def SVG_path(path, transform=None, simplify=False):
    """Construct the vertices and SVG codes for the path

    Parameters
    ----------
    path : matplotlib.Path object

    transform : matplotlib transform (optional)
        if specified, the path will be transformed before computing the output.

    Returns
    -------
    vertices : array
        The shape (M, 2) array of vertices of the Path. Note that some Path
        codes require multiple vertices, so the length of these vertices may
        be longer than the list of path codes.
    path_codes : list
        A length N list of single-character path codes, N <= M. Each code is
        a single character, in ['L','M','S','C','Z']. See the standard SVG
        path specification for a description of these.
    """
    if transform is not None:
        path = path.transformed(transform)

    vc_tuples = [(vertices if path_code != Path.CLOSEPOLY else [],
                  PATH_DICT[path_code])
                 for (vertices, path_code)
                 in path.iter_segments(simplify=simplify)]

    if not vc_tuples:
        # empty path is a special case
        return np.zeros((0, 2)), []
    else:
        vertices, codes = zip(*vc_tuples)
        vertices = np.array(list(itertools.chain(*vertices))).reshape(-1, 2)
        return vertices, list(codes)


def get_path_style(path):
    """Get the style dictionary for matplotlib path objects"""
    style = {}
    style['alpha'] = path.get_alpha()
    if style['alpha'] is None:
        style['alpha'] = 1
    style['edgecolor'] = color_to_hex(path.get_edgecolor())
    style['facecolor'] = color_to_hex(path.get_facecolor())
    style['edgewidth'] = path.get_linewidth()
    style['dasharray'] = get_dasharray(path)
    style['zorder'] = path.get_zorder()
    return style


def get_line_style(line):
    """Get the style dictionary for matplotlib line objects"""
    style = {}
    style['alpha'] = line.get_alpha()
    if style['alpha'] is None:
        style['alpha'] = 1
    style['color'] = color_to_hex(line.get_color())
    style['linewidth'] = line.get_linewidth()
    style['dasharray'] = get_dasharray(line)
    style['zorder'] = line.get_zorder()
    return style


def get_marker_style(line):
    """Get the style dictionary for matplotlib marker objects"""
    style = {}
    style['alpha'] = line.get_alpha()
    if style['alpha'] is None:
        style['alpha'] = 1

    style['facecolor'] = color_to_hex(line.get_markerfacecolor())
    style['edgecolor'] = color_to_hex(line.get_markeredgecolor())
    style['edgewidth'] = line.get_markeredgewidth()

    style['marker'] = line.get_marker()
    markerstyle = MarkerStyle(line.get_marker())
    markersize = line.get_markersize()
    markertransform = (markerstyle.get_transform()
                       + Affine2D().scale(markersize, -markersize))
    style['markerpath'] = SVG_path(markerstyle.get_path(),
                                   markertransform)
    style['zorder'] = line.get_zorder()
    return style


def get_text_style(text):
    """Return the text style dict for a text instance"""
    style = {}
    style['alpha'] = text.get_alpha()
    if style['alpha'] is None:
        style['alpha'] = 1
    style['fontsize'] = text.get_size()
    style['color'] = color_to_hex(text.get_color())
    style['halign'] = text.get_horizontalalignment()  # left, center, right
    style['valign'] = text.get_verticalalignment()  # baseline, center, top
    style['rotation'] = text.get_rotation()
    style['zorder'] = text.get_zorder()
    return style


def get_axis_properties(axis):
    """Return the property dictionary for a matplotlib.Axis instance"""
    props = {}
    label1On = axis._major_tick_kw.get('label1On', True)

    if isinstance(axis, matplotlib.axis.XAxis):
        if label1On:
            props['position'] = "bottom"
        else:
            props['position'] = "top"
    elif isinstance(axis, matplotlib.axis.YAxis):
        if label1On:
            props['position'] = "left"
        else:
            props['position'] = "right"
    else:
        raise ValueError("{0} should be an Axis instance".format(axis))

    props['nticks'] = len(axis.get_major_locator()())

    # Use tick values if appropriate
    locator = axis.get_major_locator()
    if isinstance(locator, ticker.FixedLocator):
        props['tickvalues'] = list(locator())
    else:
        props['tickvalues'] = None

    # Find tick formats
    formatter = axis.get_major_formatter()
    if isinstance(formatter, ticker.NullFormatter):
        props['tickformat'] = ""
    elif not any(label.get_visible() for label in axis.get_ticklabels()):
        props['tickformat'] = ""
    else:
        props['tickformat'] = None

    return props


def image_to_base64(image):
    """
    Convert a matplotlib image to a base64 png representation

    Parameters
    ----------
    image : matplotlib image object
        The image to be converted.

    Returns
    -------
    image_base64 : string
        The UTF8-encoded base64 string representation of the png image.
    """
    ax = image.axes
    binary_buffer = io.BytesIO()

    # image is saved in axes coordinates: we need to temporarily
    # set the correct limits to get the correct image
    lim = ax.axis()
    ax.axis(image.get_extent())
    image.write_png(binary_buffer)
    ax.axis(lim)

    binary_buffer.seek(0)
    return base64.b64encode(binary_buffer.read()).decode('utf-8')
