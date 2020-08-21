# -*- coding: utf-8 -*-
"""
Created on Wed Aug 19 12:41:26 2020

@author: MHerzo
"""

"""
For iPython/Spyder
"""

from PIL import Image
import glob
import os
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import math
#import tensorflow as tf

def get_mask_values(img):
    input_type = None
    if type(img) == str:
        input_type = 'str'
    elif type(img) == np.ndarray:
        input_type = 'array'
    
    img_obj = None
    if input_type == 'str':
        img_obj =  Image.open(img)
    elif input_type == 'array':
        img_a = img
    else:
        img_obj = img
        
    if img_obj:
        img_a = np.asarray(img_obj)
    return set(img_a[np.nonzero(img_a)])

#https://stackoverflow.com/questions/46615554/how-to-display-multiple-images-in-one-figure-correctly/46616645
# https://matplotlib.org/tutorials/introductory/images.html
#%matplotlib inline

#pattern = r'C:\Users\mherzo\Box Sync\Herzog_Michael - Personal Folder\2020\Machine Vision Misc\Image Annotation\util\export_images\**\*mask*.png'

#pattern = r'C:\Users\mherzo\Box Sync\Herzog_Michael - Personal Folder\2020\Machine Vision Misc\Image Annotation\util\export_images\**\*.png'
pattern = r'm:\msa\util\export_images\**\*mask*.png'
file_list = glob.glob(pattern, recursive=True)
df = pd.DataFrame({'file_path':file_list})
df['basename'] = df['file_path'].map(lambda x:os.path.basename(x))
df['subdir'] = df['file_path'].map(lambda x:x.split(os.sep)[-3])
df['hist'] = None
df['hist'].astype(object)

columns = 1
rows = math.ceil(len(df) / columns)

#fig = plt.figure(figsize=(3, 4))
#fig, ax = plt.subplots(nrows=rows,ncols=columns)
#fig = plt.figure()

img_num = 0
for idx in df.sort_values(['basename','file_path'],ascending=False).index:
    #split = img_path.split(os.sep)
    row = df.loc[idx]
    img = Image.open(row['file_path'])
    
    img_a = np.asarray(img)
    df.loc[idx,'hist'] = get_mask_values(img_a)
    print(row['subdir'], row['basename'])
    
    #https://stackoverflow.com/questions/37152031/numpy-remove-a-dimension-from-np-array
    img_a_bw = img_a[:,:,0].copy()
    img_a_bw[np.nonzero(img_a_bw)] = 255

    # https://stackoverflow.com/questions/10607468/how-to-reduce-the-image-file-size-using-pil
    #x, y = img.size
    #scale_factor = 0.5
    #x2, y2 = math.floor(x * scale_factor), math.floor(y * scale_factor)

    #img_small = img.resize((x2,y2),Image.ANTIALIAS)
    #img_small = img.resize((x2,y2))

    # https://stackoverflow.com/questions/44955656/how-to-convert-rgb-pil-image-to-numpy-array-with-3-channels
    #img_small = img_small.convert("RGB")
    #img_small = np.asarray(img_small, dtype=np.float32) / 255
    #img_small = img_small[:, :, :3]
    
    #img_small = img.copy()
    #img_small.thumbnail((x2,y2))
    #ax.append( fig.add_subplot(rows, columns, idx+1) )
    #plt.imshow(img_small)
    #plt.imshow(tf.keras.preprocessing.image.array_to_img(np.asarray(img)))
    plt.imshow(img_a_bw)
    plt.axis('off')
    plt.axis("tight")  # gets rid of white border
    plt.axis("image")  # square up the image instead of filling the "figure" space
    plt.title(f'#{idx}, hist={row["hist"]} type={row["subdir"]}, img={row["basename"]})')
    plt.show()    
    #break
    if img_num > 0 and img_num % 10 == 0:
        ans = input(f'Img {img_num}.  Enter any character (e.g. q) to quit: ')
        if ans:
            break
    img_num += 1
print('complete')

