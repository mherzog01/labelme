# -*- coding: utf-8 -*-
"""
Created on Thu Sep  3 15:50:53 2020

@author: MHerzo
"""

import cv2
import numpy as np
from shapely.geometry import Polygon

# For testing
from labelme import user_extns
from PIL import Image


##################################################
# Shapely/docs/figures.py 
# ------------------------------------------------
from matplotlib import pyplot as plt
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






#---------------------------
# Get polygon
#
# Use a class to ca
class MaskToPolygon():
    def __init__(self):
        self.kernel = np.ones((10,10),np.uint8)
        
    def get_polygon(self, pred_mask):
      
        self.pred_mask = pred_mask
        
        pred_mask_img = pred_mask.astype(np.uint8)
        pred_closed = cv2.morphologyEx(pred_mask_img, cv2.MORPH_CLOSE, self.kernel)
        pred_closed = cv2.morphologyEx(pred_closed, cv2.MORPH_OPEN, self.kernel)
        # TODO Use hierarchy of Canny edges to get rid of interior edges:  https://stackoverflow.com/a/15867297/11262633
        self.edges = cv2.Canny(pred_closed,0,1,L2gradient=True)
      
        # Convert to polygon, and simplify
        # https://docs.opencv.org/trunk/d4/d73/tutorial_py_contours_begin.html
        self.contours, self.hierarchy = cv2.findContours(self.edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
      
        # Using cv2.RETR_EXTERNAL, take contour with the largest area.  E.g. 20200211-151331-Img.bmp
        max_area = 0
        self.polygon = None
        for c in self.contours:
            p = Polygon(c[:,0])
            if p.area > max_area:
                self.polygon = p
                self.contour = c
      
        # Simplify
        # TODO Set tolerance based on image size?
        self.polygon_s = self.polygon.simplify(1.5)
      
        return self.polygon_s


    def disp_imgs(self, in_img=None):

        img_list = []
        if not in_img is None:
            # TODO Consolidate add_overlay and other utilities (also in gcp_lib.py)
            img_with_edges = self.add_overlay(in_img, self.edges)
            img_list.append(img_with_edges)

        img = np.zeros(self.edges.shape)
        img = cv2.drawContours(img,[self.contour],0,1,1)
        print(set(img.ravel()))
        img_list.append(img)
        
        display(img_list)        
        
        fig = plt.figure(1, figsize=SIZE, dpi=90)
        ax = fig.add_subplot(121)
        plot_coords(ax, self.polygon.exterior)
        plt.show()
        print(f'# points in polygon len={len(self.polygon_s.exterior.coords)}')


    def add_overlay(self, in_img, overlay, color=(1,0,0)):
      out_img = in_img.copy()
      #print(f'Out img shape={out_img.shape}.  Overlay shape={overlay.shape}')
      #print(f'Nonzero {overlay.nonzero()[:2]}')
      out_img[overlay.nonzero()[:2]] = color    # Image is normalized
      return out_img  
    

if __name__ == '__main__':

    # TODO Move to Tests. Segregate user_extns tests from other tests.
    img_path = r'c:\tmp\work1\20200211-151331-Img.bmp'
    cred_path = r'c:\tmp\work1\Tissue Defect UI-ML Svc Acct.json'
    
    ipm = user_extns.ImgPredMgr()
    ipm.set_cred(cred_path)
    
    img = Image.open(img_path)
    ipm.predict_imgs([img])
    for idx, m_np in enumerate(ipm.pred_masks_np):
        print(idx, m_np.shape)
        
    for img_resized, mask in zip(ipm.resized_images, ipm.pred_masks_np):
        overlay = ipm.add_overlay(img_resized, mask)
        display([img_resized, mask, overlay])         

    m_to_p = MaskToPolygon()
    m_to_p.get_polygon(mask)
    m_to_p.disp_imgs(img_resized)
