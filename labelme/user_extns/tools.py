# -*- coding: utf-8 -*-
"""
Created on Tue Feb 18 10:44:36 2020

@author: MHerzo
"""

import labelme
from labelme import user_extns
from labelme.shape import Shape
from labelme import LabelFile

import os
import os.path as osp

from qtpy import QtCore, QtWidgets, QtGui
from qtpy.QtWidgets import QWidget
from qtpy.QtWidgets import QInputDialog
from PyQt5.QtCore import QCoreApplication

from PyQt5.QtWidgets import QApplication

import sys
import glob
import pandas as pd

import tempfile
import shutil

# https://www.sqlitetutorial.net/sqlite-python/sqlite-python-select/
import sqlite3
from sqlite3 import Error

import PIL 
from PIL import Image


dev_db=r'c:\tmp\work1\images.db3'
prod_db=r'C:\Runtime\Tissue_Image_Collection\Data\images.db3'
if os.path.isfile(prod_db):
    DB_FILE=prod_db
else:
    DB_FILE=dev_db
    

#https://www.tutorialspoint.com/pyqt/pyqt_qinputdialog_widget.htm
class inputdialog(QWidget):
   def __init__(self, msg, title='Enter Information', parent = None, default_value=None):
      super(inputdialog, self).__init__(parent)
		
      self.show()
      
      text, ok = QInputDialog.getText(self, title, msg, text=default_value)
      
		
      if ok:
          self.value = text
      else:
          self.value = None

            
            
def imgFileToLabelFileName(img_file, label_dir=None):
    label_file = osp.splitext(img_file)[0] + '.json'
    if label_dir:
        label_file_without_path = osp.basename(label_file)
        label_file = osp.join(label_dir, label_file_without_path)
    return label_file

# If more options are needed, set exec=False and use returned object to do needed config
def dispMsgBox(msg, title=None, icon=None, exec=True):
    msgBox = QtWidgets.QMessageBox()
    msgBox.setText(msg)
    msgBox.setWindowTitle(title)
    if icon == "Critical":
        msgBox.setIcon(msgBox.Critical)
    elif icon == "Question":
        msgBox.setIcon(msgBox.Question)
    elif icon == "Warning":
        msgBox.setIcon(msgBox.Warning)
    elif icon == "Information":
        msgBox.setIcon(msgBox.Information)
    if exec:
        msgBox.exec();
        return
    return msgBox
		  

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
 
    return conn

def exportByLot():
    
    while True:
    
        # Get lot number
        lot_number = inputdialog('Lot Number: ').value
        print(f'Lot # = {lot_number}')
        if lot_number is None:
            return
        
        # Get images of the lot
        col_list = ['TImestamp', 'Status', 'Comment', 'File', 'Defects']
        conn = create_connection(DB_FILE)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT ' + ','.join(col_list) + ' from IMAGES where Comment like ?',(lot_number + '%',))
            
            rows = cur.fetchall()
            show_data = False
            if show_data:
                for row in rows:
                    print(row)
        num_rows=len(rows)
        print(f'# rows found={num_rows}')
        if num_rows == 0:
            print('No rows found')
            return
    
        # Copy files to temp dir
        tempdir_root = tempfile.gettempdir()
        tempdir = os.path.join(tempdir_root,'Images for Lot Number')
        if not os.path.isdir(tempdir):
            os.mkdir(tempdir)
        else:
            for file in os.scandir(tempdir):
                    os.unlink(file.path)
        file_pos = col_list.index('File')
        for idx,row in enumerate(rows):
            file = row[file_pos]
            shutil.copy(file,tempdir)
            if idx == 0:
                first_file = file 
        with open(os.path.join(tempdir,f'Lot {lot_number}.txt'),'w') as f:
            f.write(f'Images in lot {lot_number}:\n')
            for row in rows:
                print(row,file=f)
        #launchExternalViewer(first_file)
        os.system(f'start explorer "{tempdir}"')


def launchExternalViewer(filename):
    # Using PIL opens image in a temp file
    # Using 
    #   os.system(fr'start "Pillow" /WAIT "{filename}"')
    # does not allow for scrolling to other pictures.  However, this seems like the best option
    # Using
    #   fr'rundll32 "C:\Program Files\Windows Photo Viewer\PhotoViewer.dll",ImageView_Fullscreen "{filename}"'
    # doesn't support spaces in the image file name
    cmd = fr'start "Pillow" /WAIT "{filename}"'
    print(cmd)
    os.system(cmd)
    print('after')
    

# Exports a separate single-bit file for each image/defect combination    
def exportAnnotationsForImage(img_file, label_dir):
    
    export_folder = r'c:\tmp\annotation_exports'
    img_basename = osp.splitext(osp.basename(img_file))[0]
    export_basepath = osp.join(export_folder,img_basename + '_export')
    
    for f in glob.glob(export_basepath + '*.png'):
        os.remove(f)

    label_file = user_extns.imgFileToLabelFileName(img_file, label_dir)
    labelFile = labelme.LabelFile(label_file)    
    labels_to_export = set([shape['label'] for shape in labelFile.shapes])
    print(f'labels_to_export={labels_to_export}')
    for label in labels_to_export:
        shapes_to_export = [s for s in labelFile.shapes if s['label'] == label]
        #print(f'shapes_to_export={shapes_to_export}')
        print(f'# shapes_to_export for {label}={len(shapes_to_export)}')

        # Load image to initialize the pixmap to the proper size
        # Then, set all pixels to 0
        # TODO Make more efficient.  Don't load file.  Create empty image with right size/attributes
        pixmap = QtGui.QPixmap(img_file)
        pixmap.fill(QtGui.QColor(0,0,0))
        # Paint annotations
        # TODO Centralize annotation painting logic -- it exists here and several other places (app.exportMasks, etc.).  Use util/shape_to_mask or examples/.../draw_json.py
        p = QtGui.QPainter(pixmap)
        for s in shapes_to_export:
            s_obj = Shape(label=s['label'], shape_type=s['shape_type'],
             flags=s['flags'], group_id=s['group_id'])
            for pt in s['points']:
                s_obj.addPoint(QtCore.QPointF(pt[0],pt[1]))
            s_obj.close = True
            s_obj.fill = True
            s_obj.point_size = 0
            s_obj.paint(p)
        p.end()
        img_to_export = pixmap.toImage()
        img_to_export.convertToFormat(QtGui.QImage.Format_Indexed8)
        
        targ_file = export_basepath + f'_{label.replace("/","")}.png'
        #TODO Move to PIL without saving to disk in order 
        img_to_export.save(targ_file)
                
        img_tmp = PIL.Image.open(targ_file)
        img_tmp = img_tmp.convert("L")
        img_tmp.save(targ_file)    

    
    
def exportAnnotationsFromImageDir():
    img_dir = r'C:\Users\mherzo\AppData\Roaming\Cognex Corporation\Cognex ViDi Suite 3.4\workspaces\MH Test Vidi Workspace\b36e3836-b906-44ab-ac9a-a318102e9ea3\images'
    for f in glob.glob(img_dir + r'\*'):
        print(f)
        if osp.basename(f) < '20200211' or osp.basename(f)[:4] == 'Img-':
            continue
            #label_dir = r'D:\Tissue Defect Inspection\Images3'
        else:
            label_dir = r'D:\Tissue Defect Inspection\Images4'
        exportAnnotationsForImage(f, label_dir)
        #break
        
        
#https://stackoverflow.com/questions/34275782/how-to-get-desktop-location        
#os.environ["HOMEPATH"] doesn't work in VDI - gives \\users\mherzo, not c:\users\mherzo
#VDI desktop is at \\Allergan.com\VDI\Users\MHerzo\Desktop
# Assume local desktop is of form c:\users\mherzo\Desktop
def getDesktop():
    desktop_local = osp.join(os.path.expanduser("~"),'desktop')
    if osp.exists(desktop_local):
        return desktop_local
    else:
        desktop_vdi = osp.join(r'\\Allergan.com\VDI', desktop_local[3:])
        return desktop_vdi
        
    
def getAnnotDf(file_list, status_callback=None):
    
    annot_c = AnnotDf(status_callback)
    annot_c.load_files(file_list)
    return annot_c.df_annot


class AnnotDf():

    def __init__(self,
                 status_callback=None):
        # Assume:
        #   - .json are in same directory as files in file_list
        self.df_annot = pd.DataFrame(columns=['image_path',
                                              'image_basename',
                                              'annot_num',
                                              'label',
                                              'group_id'])
        self.df_annot.astype({'image_path':str,
                              'image_basename':str,
                              'annot_num':int,
                              'label':str,
                                        'group_id':int})
        self.status_callback = status_callback
    
    
    #def get_flag_value(self, flag_dict, flag_key):
    #    return (flag_key in flag_dict and flag_dict[flag_key])
    
    def stat_msg(self, msg):
        if self.status_callback:
            self.status_callback(msg)
        else:
            print(msg)

    def load_files(self, file_list):
        
        for img_file in file_list:
            
            #img_date = datetime.datetime.strptime(row[0].split(' ')[0],'%Y-%m-%d')
            self.stat_msg(f'File {img_file}.')
            label_file = user_extns.imgFileToLabelFileName(img_file, osp.dirname(img_file))
            if not osp.exists(label_file):
                self.load_shape(img_file)
                #stat_msg(f'No label file {label_file} found for image file {img_file}.')
                continue
            #img_basename = osp.basename(img_file)
            labelFile = LabelFile(label_file, loadImage=False)    
            #img_unique_labels = set([shape['label'] for shape in labelFile.shapes])
            #print(f'File {img_file}.  img_unique_labels={img_unique_labels}')
            self.load_shapes(img_file, labelFile.shapes)

    def load_shapes(self,img_file, shape_list):
        annot_num = 0
        for shape in shape_list:
            annot_num += 1 
            flag_dict = shape['flags']
            label = shape['label']
            group_id = shape['group_id']
            # not_in_picture = self.get_flag_value(flag_dict, 'Not in picture')
            # not_in_tissue = self.get_flag_value(flag_dict, 'Not in tissue')
            # review_recommended = self.get_flag_value(flag_dict, 'Review recommended')
            # rework = self.get_flag_value(flag_dict, 'Rework')
            self.load_shape(
                       img_file,
                       annot_num,
                       label,
                       group_id,
                       flag_dict)
            #break
        if annot_num == 0:
            self.load_shape(img_file)

    def load_shape(self,
                   img_file,
                   annot_num = 0,
                   label = None,
                   group_id = None,
                   flag_dict = None):
        key = len(self.df_annot)
        self.df_annot.loc[key, 'image_path'] = img_file
        self.df_annot.loc[key, 'image_basename'] = osp.basename(img_file)
        self.df_annot.loc[key, 'annot_num'] = annot_num
        self.df_annot.loc[key, 'label'] = label
        self.df_annot.loc[key, 'group_id'] = group_id
        if flag_dict:
            for flag in flag_dict:
                col_name = flag.replace(' ','_')
                # No need to create columns.  Assignment via .loc[key,col] creates if needed
                #if not col_name in self.df_annot.columns:
                self.df_annot.loc[key, col_name] = flag_dict[flag]
    
    
if __name__ == '__main__':
    app = QCoreApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    #msgBox = dispMsgBox('1', '2', icon='Warning')
    #msgBox.exec()
    
    #sys.exit(app.exec_())
    #x = user_extns.getAnnotDf(glob.glob(r'm:\msa\annot\Ground Truth\*.bmp'))
    def cb(msg):
        print('cb:' + msg)
    x = getAnnotDf(glob.glob(r'm:\msa\annot\Ground Truth\*.bmp'), cb)
    print(f'x={x}')
    