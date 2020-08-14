# -*- coding: utf-8 -*-
"""
Created on Mon Aug 10 16:23:19 2020

@author: MHerzo

Create a report for browsing annotaiton details.

- For each image, generate an image with the annotations on it.

- For each annotation on an image, generates a .png image 
  and a .json file for that annotation

- Generate HTML file which displays an image of each annotation, with the ability to view
  an image of the entire piece of tissue, with or without annotations


Assumptions
1.  Images are in a single folder, or the list of images is unique by image basename
2.  .json file for images (if it exists), is in the same folder as the image

TODO *** Scan entire list below for priority tasks
1. Improve performance of report
- Use styles, not object-level HTML (e.g. onclick)
- Break into separate files
2. If click on image text, select whole image name
3. **Display of defects, ensure some value is shown.  E.g. 20200306-154951-Img.bmp, Annot #7 - center and point on circle are the same:
        {
      "label": "Residual Epi",
      "points": [
        [
          2688.0,
          1640.625
        ],
        [
          2688.0,
          1640.625
        ]
      ],
      "group_id": 5,
      "shape_type": "circle",
      "flags": {
        "Rework": true,
        "Not in picture": false,
        "Not in tissue": false,
        "Review recommended": false
      }
    },
4.  Compute and display area of each annotation
5.  Create map for each image - hover over each annotation and see different values
6.  Double click on defect and launch LabelMe for that image
7.  * In last section, images with no defects are not displayed.  nan is shown instead.
8.  *** Create table of contents (by label)
9.  ** Set title of report .html file
10.  Display lot number.  Requires using database -- centralize annotations with data set?
"""


from os import path as osp
import glob
import labelme
import os
from labelme import user_extns
from labelme.shape import Shape
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
from PIL import Image
import sys
import imgviz
import numpy as np
import string
import shutil
import datetime
import pandas as pd

def get_defect_intensity(group_id):
    return str(group_id) if not group_id == float('nan') else 'None'

#------------------------------------------
# Settings
module_folder = osp.dirname(__file__)
template_path = osp.join(module_folder,'rpt01_template.html')
label_dir = r'\\ussomgensvm00.allergan.com\lifecell\Depts\Tissue Services\Tmp\MSA\Annot\Ground Truth'
export_root = osp.join(label_dir, '..','..','util','export_images')
export_img_dir = osp.join(export_root,'annotation_exports')
export_annot_dir = osp.join(export_root,'annotation_exports')
#label_dir = r'c:\tmp\work4'
selection_margin = 100  # Number of pixels that surround the selected area of the image
create_img_exports = ['all','new','none'][1]  
create_annot_exports = [ 'all','none'][0]
#------------------------------------------

if create_annot_exports == 'all':
    create_annot_images = True
else:
    create_annot_images = False
            
# The report depends on current state of image annotations, so prior versions may not have integrity
#rpt_stem = 'rpt01'
#rpt_name = f'{rpt_stem}_{datetime.datetime.now():%Y%M%D_%h%m%s}.html'
rpt_basename = 'rpt01.html'
rpt_path = osp.join(export_root, rpt_basename)

LABEL_COLORMAP = user_extns.get_colormap()
num_labels = len(LABEL_COLORMAP)


image_list = []

if osp.exists(rpt_path):
    os.remove(rpt_path)

# TODO Mouse over defect type and severity
# TODO Comments
# TODO Lot number
c_annot = user_extns.AnnotDf()
df_annot = c_annot.df_annot
df_annot['divs'] = ''

# Needed to paint shapes
app = QtWidgets.QApplication(sys.argv)
    
label_colors = {}
img_num = -1
for img_path in glob.glob(osp.join(label_dir,"*.bmp")):

    df_annot.load_file(img_path)
    img_basename = df_annot.cur_image_basename
    img_num += 1
    print(f'{datetime.datetime.now():%Y-%m-%d %H:%M:%S} Image={img_basename}')
    
    img_basestem, img_ext = osp.splitext(img_basename)
    export_img_basename = img_basestem + '_export.png'
    export_img_path = osp.join(export_img_dir,export_img_basename)
    
    if create_img_exports == 'all':
        create_image = True
    elif create_img_exports == 'none':
        create_image = False
    elif create_img_exports == 'new':
        create_image = not osp.exists(export_img_path)        

    image_list.append([img_path, export_img_path])
    
    # Delete files one at a time to allow updates of individual files
    if create_image and osp.exists(export_img_path):
        os.remove(export_img_path)
    
    # Delete all annotations of the image to allow for annotation changes
    if create_annot_images:
        for file in glob.glob(osp.join(export_annot_dir,img_basestem + '*.png')):
            os.remove(file)

        
    label_file = user_extns.imgFileToLabelFileName(img_basename, label_dir)
    labelFile = labelme.LabelFile(label_file, loadImage=False)    

    img_pixmap = QtGui.QPixmap(img_path)
    img_size = img_pixmap.size()
    # Paint annotations
    # TODO Centralize annotation painting logic -- it exists here and several other places (app.exportMasks, etc.).  Use util/shape_to_mask or examples/.../draw_json.py
    # TODO don't paint if 'create_image' == False
    p_img = QtGui.QPainter(img_pixmap)
    shapes_to_export = labelFile.shapes
    export_annot_basestem = f'{img_basestem}_export_'
    for annot_idx, s in enumerate(shapes_to_export):
        annot_num = annot_idx + 1
        s_obj = Shape(label=s['label'], shape_type=s['shape_type'],
          flags=s['flags'], group_id=s['group_id'])
        first_pt_q = None

        label = s_obj.label
        # TODO *Make colors consistent with labelMe
        if not label in label_colors:
            label_colors[label] = QtGui.QColor(*LABEL_COLORMAP[len(label_colors) % num_labels])
        
        # TODO More pythonic way of handing min/max x/y
        min_w, max_w, min_h, max_h = (img_size.width(),0,img_size.height(),0)
        for pt in s['points']:
            pt_q = QtCore.QPointF(pt[0],pt[1])
            if not first_pt_q:
                first_pt_q = pt_q
            s_obj.addPoint(pt_q)
            min_w = min(min_w, pt[0])
            max_w = max(max_w, pt[0])
            min_h = min(min_h, pt[1])
            max_h = max(max_h, pt[1])
        s_obj.addPoint(first_pt_q)
        #s_obj.close = True
        s_obj.fill = False
        s_obj.point_size = 0
        # TODO - draw text label and shape # of annotation next to shape
        # TODO Get the scale value more intelligently?  canvas.scale -> widget scale factor via canvas.update?
        s_obj.scale = 1 / 2
        s_obj.line_color = label_colors[label]
        s_obj.paint(p_img)
        
        # Get bounding region of image.  ll = Lower Left, ur = Upper Right
        roi_ll = (max(0,min_w - selection_margin), min(img_size.height(),max_h + selection_margin))
        roi_ur = (min(img_size.width(),max_w + selection_margin), max(0,min_h - selection_margin))
        
        # Add to image_divs
        img_div_width = roi_ur[0] - roi_ll[0]
        img_div_height = roi_ll[1] - roi_ur[1]
        
        # ------------------
        margin_top = roi_ur[1]
        margin_left = roi_ll[0]
        
        if create_annot_images:
            # https://stackoverflow.com/questions/25795380/how-to-crop-a-image-and-save
            roi_ll_q = QtCore.QPoint(margin_left,margin_top)
            roi_q = QtCore.QRect(roi_ll_q,QtCore.QSize(img_div_width,img_div_height))
            annot_pixmap = img_pixmap.copy(roi_q)

            # Unannotated image
            export_annot_basename = export_annot_basestem + f'{s_obj.label}_{annot_idx}.png'
            export_annot_path = osp.join(export_annot_dir,export_annot_basename)        
            annot_pixmap.save(export_annot_path)

            # Annotated image
            disp_annot_on_img = True
            if disp_annot_on_img:
                points_tmp = []
                for pt_q in s_obj.points:
                    points_tmp += [pt_q - roi_ll_q]
                s_obj.points = points_tmp
                p = QtGui.QPainter(annot_pixmap)
                s_obj.paint(p)
                p.end()
            annot_pixmap.save(export_annot_path)
        
        # ------------------

        img_id = f'{img_basename},{annot_num}'
        
        image_divs = ''
        image_divs += f'<div class="crop">\n'
        image_divs += f'  <div class="crop" style="width:{img_div_width};height:{img_div_height}" '
        image_divs += f'       onclick="getimage(\'{img_id}\',{img_num})"'
        image_divs += f'       title="{s_obj.label}, Intensity: {get_defect_intensity(s_obj.group_id), {img_basename}}">\n'
        image_divs += f'    <img id="{img_id}" src="{export_img_path}" alt="{img_basename} {s_obj.label}" style="margin-top:-{margin_top};margin-left:-{margin_left};">\n'
        image_divs += f'  </div>\n'
        image_divs += f'  <div style="width:{img_div_width}">\n'
        image_divs += f'    {img_basename}, {annot_num}\n'
        if any(s_obj.flags.values()):
            image_divs += f'    <br>{", ".join([key for key in s_obj.flags if s_obj.flags[key]])}\n'
        image_divs += f'    <div style="height:5"></div>\n'
        image_divs += f' </div>\n'
        image_divs += f' </div>\n'
        df_divs.loc[(img_basename,annot_num),'Div'] = image_divs
    
    p_img.end()
    
    if create_image:
        img_pixmap.save(export_path)

# 1.  Write HTML header (script) and report header [*Template needed]
# 2.  For each label
#        Write section header
#        Write divs [*Template needed]

image_divs = ''
prev_label = None
prev_grp = None
for idx in df_annot.sort_values(['label','group_id','image_basename','annot_num']).index:
    row = df_annot.loc[idx]
    cur_label = row['label']
    cur_grp = row['group_id']
    if not prev_label or prev_label != cur_label:
        image_divs += f'<h2>{cur_label}</h2>\n'
        prev_label = cur_label
        prev_grp = None
        new_label = True
    else:
        new_label = False
    if new_label or prev_grp != cur_grp:
        image_divs += f'<h3>Defect Intensity: {get_defect_intensity(cur_grp) }</h3>\n'
        prev_grp = cur_grp
    image_divs += df_divs.loc[(row['image_basename'],row['annot_num']),'Div']
        
#TODO Move to PIL without saving to disk in order 
#img_tmp = Image.open(targ_f.ile)
#img_tmp = img_tmp.convert("L")
#img_tmp.save(targ_file)    

xref = {'basedir':export_folder.replace('\\','/'),
        'image_array':image_list,    # In javascript, the Python list is an array
        'image_divs':image_divs}
with open(rpt_path,'w') as f_o:
    with open(template_path) as f_t:
        for in_line in f_t:
            out_line = in_line
            # Escape $
            out_line = out_line.replace('$','$$')
            # Substitute $ for %
            out_line = out_line.replace('%','$')
            template = string.Template(out_line)
            out_line = template.substitute(xref)
            f_o.write(out_line)

# TODO * Handle errors - clean up painter 