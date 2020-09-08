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
from labelme.user_extns import img_ml_util
from PIL import Image


##################################################
# Shapely/docs/figures.py 
# ------------------------------------------------
from matplotlib import pyplot as plt

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
# Use a class to store intermediate data such as edges and contours
class MaskToPolygon():
    def __init__(self, targ_size : (int,int) = None):
        self.targ_size=targ_size
        self.kernel = np.ones((10,10),np.uint8)
        #self.simplification_limits = (1,2)
        #self.simlification_len = 25  # Desired number of pixels between points of polygon
        
    def get_polygon(self, pred_mask, scale_points=True):
      
        if scale_points and self.targ_size is None:
            print('ERROR:  point scaling was requested but no target size was provided')
            raise ValueError
            
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
        # TODO Set tolerance based on polygon length, with a min and max ratio
        #polygon_len = self.polygon.length
        #orig_num_pts = len(self.polygon.boundary.coords)
        self.polygon_s = self.polygon.simplify(1.5)
      
        if scale_points:
            scale_x = self.targ_size[0] / pred_mask.shape[0]
            scale_y = self.targ_size[1] / pred_mask.shape[1]
            self.scale_factor = (scale_x, scale_y)
            self.polygon_s = affinity.scale(self.polygon_s, xfact=scale_x, yfact=scale_y, origin=(0,0))
            #TODO Scale self.polygon and self.contour?

        self.boundary_pts = self.polygon_s.boundary.coords

        return self.boundary_pts


    def disp_imgs(self, in_img=None):

        img_list = []
        if not in_img is None:
            # TODO Consolidate add_overlay and other utilities (also in gcp_lib.py)
            img_with_edges = img_ml_util.add_overlay(in_img, self.edges)
            img_list.append(img_with_edges)

        img = np.zeros(self.edges.shape)
        img = cv2.drawContours(img,[self.contour],0,1,1)
        print(set(img.ravel()))
        img_list.append(img)
        
        img_ml_util.display(img_list)        
        
        fig = plt.figure(1, figsize=SIZE, dpi=90)
        ax = fig.add_subplot(121)
        plot_coords(ax, self.polygon.boundary.coords)
        plt.show()
        print(f'# points in original polygon len={len(self.polygon.boundary.coords)}')

        fig = plt.figure(1, figsize=SIZE, dpi=90)
        ax = fig.add_subplot(121)
        plot_coords(ax, self.boundary_pts)
        plt.show()
        print(f'# points in final polygon len={len(self.boundary_pts)}')
    

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
        overlay = img_ml_util.add_overlay(img_resized, mask)
        img_ml_util.display([img_resized, mask, overlay])         

    m_to_p = MaskToPolygon()
    m_to_p.get_polygon(mask, scale_points=False)
    m_to_p.disp_imgs(img_resized)

    m_to_p.targ_size = img.size
    m_to_p.get_polygon(mask)
    m_to_p.disp_imgs(img_resized)
