# -*- coding: utf-8 -*-
"""
Created on Fri Sep  4 14:52:56 2020

@author: MHerzo
"""


    
    
# Utility functions for displaying images/debugging process
def display_img(img):
    plt.axis('off')
    #plt.axis("tight")  # gets rid of white border
    #plt.axis("image")  # square up the image instead of filling the "figure" space
    # Disable display if running the Spyder Profiler
    if True:
        plt.imshow(img)
        plt.show()
    else:
        print(f'Display of img {img_np.shape} disabled')

# TODO:  Display all images in list horizontally
def display(img_list):
    for img in img_list:
        display_img(img)    


def add_overlay(in_img, overlay, color=(1,0,0)):
    if isinstance(in_img, np.ndarray):
        out_img = in_img.copy()
    else:
        out_img = np.asarray(in_img).copy()

    if not isinstance(overlay, np.ndarray):
        overlay = np.asarray(overlay)
    #print(f'Out img shape={out_img.shape}.  Overlay shape={overlay.shape}')
    #print(f'Nonzero {overlay.nonzero()[:2]}')
    out_img[overlay.nonzero()[:2]] = color    # Image is normalized
    return out_img  