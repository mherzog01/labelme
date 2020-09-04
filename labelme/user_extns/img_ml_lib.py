# -*- coding: utf-8 -*-
"""
Created on Thu Sep  3 15:50:53 2020

@author: MHerzo
"""

import cv2
import numpy as np
from shapely.geometry import Polygon


##################################################
# Shapely/docs/figures.py 
# ------------------------------------------------
from matplotlib import pyplot
from shapely.geometry import Polygon

from math import sqrt
from shapely import affinity

GM = (sqrt(5)-1.0)/2.0
W = 8.0
H = W*GM
SIZE = (W, H)

BLUE = '#6699cc'
GRAY = '#999999'
DARKGRAY = '#333333'
YELLOW = '#ffcc33'
GREEN = '#339933'
RED = '#ff3333'
BLACK = '#000000'

COLOR_ISVALID = {
    True: BLUE,
    False: RED,
}

def plot_line(ax, ob, color=GRAY, zorder=1, linewidth=3, alpha=1):
    x, y = ob.xy
    ax.plot(x, y, color=color, linewidth=linewidth, solid_capstyle='round', zorder=zorder, alpha=alpha)

def plot_coords(ax, ob, color=GRAY, zorder=1, alpha=1):
    x, y = ob.xy
    ax.plot(x, y, 'o', color=color, zorder=zorder, alpha=alpha)

def color_isvalid(ob, valid=BLUE, invalid=RED):
    if ob.is_valid:
        return valid
    else:
        return invalid

def color_issimple(ob, simple=BLUE, complex=YELLOW):
    if ob.is_simple:
        return simple
    else:
        return complex

def plot_line_isvalid(ax, ob, **kwargs):
    kwargs["color"] = color_isvalid(ob)
    plot_line(ax, ob, **kwargs)

def plot_line_issimple(ax, ob, **kwargs):
    kwargs["color"] = color_issimple(ob)
    plot_line(ax, ob, **kwargs)

def plot_bounds(ax, ob, zorder=1, alpha=1):
    x, y = zip(*list((p.x, p.y) for p in ob.boundary))
    ax.plot(x, y, 'o', color=BLACK, zorder=zorder, alpha=alpha)

def add_origin(ax, geom, origin):
    x, y = xy = affinity.interpret_origin(geom, origin, 2)
    ax.plot(x, y, 'o', color=GRAY, zorder=1)
    ax.annotate(str(xy), xy=xy, ha='center',
                textcoords='offset points', xytext=(0, 8))

def set_limits(ax, x0, xN, y0, yN):
    ax.set_xlim(x0, xN)
    ax.set_xticks(range(x0, xN+1))
    ax.set_ylim(y0, yN)
    ax.set_yticks(range(y0, yN+1))
    ax.set_aspect("equal")
##################################################

### Get polygon.

def get_polygon(in_img, pred_mask, disp_imgs=False):
    kernel = np.ones((10,10),np.uint8)
  
    pred_mask_img = pred_mask.astype(np.uint8)
    pred_closed = cv2.morphologyEx(pred_mask_img, cv2.MORPH_CLOSE, kernel)
    pred_closed = cv2.morphologyEx(pred_closed, cv2.MORPH_OPEN, kernel)
    # TODO Use hierarchy of Canny edges to get rid of interior edges:  https://stackoverflow.com/a/15867297/11262633
    edges = cv2.Canny(pred_closed,0,1,L2gradient=True)
  
    if disp_imgs:
      img_with_edges = add_overlay(in_img, edges)
  
    # Convert to polygon, and simplify
    # https://docs.opencv.org/trunk/d4/d73/tutorial_py_contours_begin.html
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
  
    # Using cv2.RETR_EXTERNAL, take the first parent
    # TODO If there is more than one parent, take largest area.  E.g. 20200211-151331-Img.bmp
    contour_p = contours[0]
  
    if disp_imgs:
      img = np.zeros(edges.shape)
      img = cv2.drawContours(img,[contour_p],0,1,1)
      print(set(img.ravel()))
      display([img_with_edges, img])
  
    # Simplify
    polygon = Polygon(contour_p[:,0])
  
    # TODO Set tolerance based on image size?
    polygon_s = polygon.simplify(1.5)
    if disp_imgs:
      fig = pyplot.figure(1, figsize=SIZE, dpi=90)
      ax = fig.add_subplot(121)
      plot_coords(ax, polygon_s.exterior)
      plt.show()
      print(f'# points in polygon len={len(polygon_s.exterior.coords)}')
  
    return polygon