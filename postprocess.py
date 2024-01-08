import os
import pandas as pd
import numpy as np
import shutil
import re
import os
import re
import shutil
import pandas as pd
from glob import glob
from PIL import Image, ImageDraw

def save_medians(directory:str):
    '''
    select the tiles where the number of cells is above global/local median
    directory: parent folder containing the subfolders representing each WSI
    returns: a csv file containing global and local medians for each WSI
    '''
    global_data = pd.DataFrame(columns=["Object ID", "Number of Tumor Cell", "Number of Immune Cell"])
    final_data = pd.DataFrame(columns=["Filename", "Global median tumor", "No. of tumor-rich tiles (global)",
                                       "Local median tumor", "No. of tumor-rich tiles (local)",
                                       "Global median immune", "No. of immune-rich tiles (global)", 
                                       "Local median immune","No. of immune-rich tiles (local)"])
    for folder in os.listdir(directory):
        if os.path.isdir(os.path.join(directory, folder)):
            detection_csv = os.path.join(directory, folder, 'detection.csv')
            if not os.path.isfile(detection_csv):
                continue
            data = pd.read_csv(detection_csv)
            global_data = pd.concat([global_data, data], ignore_index=True)
    global_median_tumor = global_data["Number of Tumor Cell"].median()
    global_median_immune = global_data["Number of Immune Cell"].median()
    print(f'Global median for tumor cells is {global_median_tumor}')
    print(f'Global median for immune cells is {global_median_immune}')
   
    for folder in os.listdir(directory):
        if os.path.isdir(os.path.join(directory, folder)):
            detection_csv = os.path.join(directory, folder, 'detection.csv')
            if not os.path.isfile(detection_csv):
                continue
            data = pd.read_csv(detection_csv)
            local_median_tumor = data['Number of Tumor Cell'].median()
            local_median_immune = data['Number of Immune Cell'].median()
            local_tumor = len(data[data["Number of Tumor Cell"] > local_median_tumor])
            local_immune = len(data[data["Number of Immune Cell"] > local_median_immune])
            global_tumor = len(data[data["Number of Tumor Cell"] > global_median_tumor])
            global_immune = len(data[data["Number of Immune Cell"] > global_median_immune])
            new_row = [folder, global_median_tumor, global_tumor, 
                    local_median_tumor, local_tumor,
                    global_median_immune, global_immune,
                    local_median_immune, local_immune]
            final_data.loc[len(final_data)] = new_row
    final_data.to_csv(os.path.join(directory, 'median.csv')) 

def save_q1s(directory:str):
    '''
    select the tiles where the number of cells is above global/local lower quartile (q1)
    directory: parent folder containing the subfolders representing each WSI
    returns: a csv file containing global and local medians for each WSI
    '''
    global_data = pd.DataFrame(columns=["Object ID", "Number of Tumor Cell", "Number of Immune Cell"])
    final_data = pd.DataFrame(columns=["Filename", "Global q1 tumor", "No. of tumor-rich tiles (global)",
                                       "Local q1 tumor", "No. of tumor-rich tiles (local)",
                                       "Global q1 immune", "No. of immune-rich tiles (global)", 
                                       "Local q1 immune","No. of immune-rich tiles (local)"])
    for folder in os.listdir(directory):
        if os.path.isdir(os.path.join(directory, folder)):
            detection_csv = os.path.join(directory, folder, 'detection.csv')
            if not os.path.isfile(detection_csv):
                continue
            data = pd.read_csv(detection_csv)
            global_data = pd.concat([global_data, data], ignore_index=True)
    global_q1_tumor = np.percentile(global_data["Number of Tumor Cell"], 25)
    global_q1_immune = np.percentile(global_data["Number of Immune Cell"], 25)
    print(f'Global q1 for tumor cells is {global_q1_tumor}')
    print(f'Global q1 for immune cells is {global_q1_immune}')
   
    for folder in os.listdir(directory):
        if os.path.isdir(os.path.join(directory, folder)):
            detection_csv = os.path.join(directory, folder, 'detection.csv')
            if not os.path.isfile(detection_csv):
                continue
            data = pd.read_csv(detection_csv)
            local_q1_tumor = np.percentile(data['Number of Tumor Cell'], 25)
            local_q1_immune = np.percentile(data['Number of Immune Cell'], 25)
            local_tumor = len(data[data["Number of Tumor Cell"] > local_q1_tumor])
            local_immune = len(data[data["Number of Immune Cell"] > local_q1_immune])
            global_tumor = len(data[data["Number of Tumor Cell"] > global_q1_tumor])
            global_immune = len(data[data["Number of Immune Cell"] > global_q1_immune])
            new_row = [folder, global_q1_tumor, global_tumor, 
                    local_q1_tumor, local_tumor,
                    global_q1_immune, global_immune,
                    local_q1_immune, local_immune]
            final_data.loc[len(final_data)] = new_row
    final_data.to_csv(os.path.join(directory, 'q1.csv')) 

def split_to_groups(folder:str):
    '''folder: absolute path to the target folder'''
    parent = os.path.dirname(folder)
    final_csv = pd.read_csv(os.path.join(parent, 'median.csv'))
    global_median = final_csv.set_index('Filename')[['Global median tumor', 'Global median immune']].to_dict()
    os.makedirs(os.path.join(folder, 'tumor'), exist_ok=True)
    os.makedirs(os.path.join(folder, 'immune'), exist_ok=True)
    # os.makedirs(os.path.join(folder, 'tumor_immune'), exist_ok=True)
    obj_id =  pd.read_csv(os.path.join(folder, 'objectID.csv'))
    obj_dict = dict(zip(obj_id['id'], obj_id['filename']))
    df = pd.read_csv(os.path.join(folder, 'detection.csv'))
    tumor = df[df['Number of Tumor Cell'] > global_median['Global median tumor'][os.path.basename(folder)]] 
    immune = df[df['Number of Immune Cell'] > global_median['Global median immune'][os.path.basename(folder)]] 
    tumor_set = set(tumor['Object ID'].tolist())
    immune_set = set(immune['Object ID'].tolist())
    tumor_files = list(tumor_set.difference(immune_set))
    immune_files = list(immune_set.difference(tumor_set))
    # for file in overlap_files:
    #     filename = obj_dict[file]
    #     src = os.path.join(folder, filename)
    #     dest = os.path.join(folder, 'tumor_immune', filename)
    #     shutil.move(src, dest)

    overlap_files  = list(tumor_set.intersection(immune_set))
    for objID in overlap_files:
        row = df[df['Object ID'] == objID]
        if row.iloc[0]['Number of Immune Cell'] > row.iloc[0]['Number of Tumor Cell']:
            immune_files.append(objID)
        else:
            tumor_files.append(objID)

    for file in tumor_files:
        filename = obj_dict[file]
        src = os.path.join(folder, filename)
        dest = os.path.join(folder, 'tumor', filename)
        shutil.move(src, dest)

    for file in immune_files:
        filename = obj_dict[file]
        src = os.path.join(folder, filename)
        dest = os.path.join(folder, 'immune', filename)
        shutil.move(src, dest)

def copy_to_merge(folder:str):
    merge = os.path.join(folder, 'merge')
    os.makedirs(merge, exist_ok=True)
    subfolders = ['blank', 'pen', 'rbc', 'fold'] 
    images = glob(os.path.join(folder, '*.png'))
    for subfolder in subfolders:
        to_copy = glob(os.path.join(folder, subfolder, '*.png'))
        for i in to_copy:
            dest = os.path.join(merge, os.path.basename(i).split('.')[0] + '.jpg')
            with Image.open(i) as img:
                img.save(dest)
    for image in images:
        dest = os.path.join(merge, os.path.basename(image).split('.')[0] +'.jpg')
        with Image.open(image) as img:
            img.save(dest)

def color_code(folder:str):
    blue = (0, 0, 255)  
    yellow = (255, 255, 0)  
    green = (0, 255, 0)  
    tumor = glob(os.path.join(folder, 'tumor', '*.png'))
    for file in tumor:
        input_image = Image.open(file)
        color_layer = Image.new('RGB', input_image.size, blue)
        output_image = Image.blend(input_image, color_layer, alpha=0.3)
        output_image.save(os.path.join(folder, 'merge', os.path.basename(file.split('.')[0]) +'.jpg'))
        print(f'save {file}')
    immune = glob(os.path.join(folder, 'immune', '*.png'))
    for file in immune:
        input_image = Image.open(file)
        color_layer = Image.new('RGB', input_image.size, green)
        output_image = Image.blend(input_image, color_layer, alpha=0.3)
        output_image.save(os.path.join(folder, 'merge', os.path.basename(file.split('.')[0])+ '.jpg'))
        print(f'save {file}')
    # tumor_immune = glob(os.path.join(folder, 'tumor_immune', '*.png'))
    # for file in tumor_immune:
    #     input_image = Image.open(file)
    #     color_layer = Image.new('RGB', input_image.size, yellow)
    #     output_image = Image.blend(input_image, color_layer, alpha=0.3)
    #     output_image.save(os.path.join(folder, 'merge', os.path.basename(file.split('.')[0])+'.jpg'))
    #     print(f'save {file}')
            
    
def x_sort_key(filename):
    '''sort the files based on x-'''
    match = re.search(r'x-(\d+)', filename)
    if match:
        return int(match.group(1))
    else:
        return 0  # Return 0 if 'x-' followed by digits is not found in the filename

def y_sort_key(filename):
    '''sort the files based on y-'''
    match = re.search(r'y-(\d+)', filename)
    if match:
        return int(match.group(1))
    else:
        return 0

def rename_all(folder:str):
    '''
    rename each tile in merge folder to prepare for merging
    from Qupath format (x-1234-y-1234-w-1234-h-1234) 
    to OpenSlide format (x_y) where x and y should start from 0 
    '''
    merge_dir = os.path.join(folder, 'merge')
    tiles = [file for file in os.listdir(merge_dir) if file.endswith(('.jpg'))]
    if len(tiles)>0:
        sorted_x = sorted(tiles, key=x_sort_key)   # original names in sorted order
        coorx = {}
        split_sorted_x = []
        for name in sorted_x:
            split_sorted_x.append(name.split('-')[1])
        for num in split_sorted_x:
            if num not in coorx:
                coorx[num] = len(coorx)
        sorted_y = sorted(tiles, key=y_sort_key)
        coory = {}
        split_sorted_y = []
        for name in sorted_y:
            split_sorted_y.append(name.split('-')[3])
        for num in split_sorted_y:
            if num not in coory:
                coory[num] = len(coory)
        for tile in tiles:
            match = re.search(r'x-(\d+)-y-(\d+)', tile)
            x = match.group(1)
            y = match.group(2)
            newx = coorx[x]
            newy = coory[y]
            os.rename(os.path.join(folder, merge_dir, tile), 
                    os.path.join(folder, merge_dir, str(newx)+'_'+str(newy)+'.jpg'))
    else:
        print('Empty directory')


if __name__ == '__main__':
    PARENT_DIR = '/Users/shihuitay/Desktop/pathomics/data/250'
    # save_medians(PARENT_DIR)
    # save_q1s(PARENT_DIR)
    # folders = [os.path.abspath(os.path.join(PARENT_DIR, p)) for p in os.listdir(PARENT_DIR) if p!= '.DS_Store' and not p.endswith('.csv') and p!= 'unwanted']
    # folders = [os.path.join(PARENT_DIR, file) for file in ['19RR000008-A-42-01_HE-STAIN_20190703_173035', '19RR060020-A-07-01_HE-STAIN_20190711_004017']]
    # folders = [os.path.join(PARENT_DIR, file) for file in ['18rr060026-a-05-01_he-stain_20180226_223447']]
    # folders = [os.path.join(PARENT_DIR, file) for file in ['21RR060004-A-21-01_HE-STAIN_20210825_143722', '21RR060004-A-29-01_HE-STAIN_20210825_150200']]
    # folders = [os.path.join(PARENT_DIR, file) for file in ["17RR060061-A-08-01_HE-STAIN_20171130_182935","18RR060016-A-18-01_HE-STAIN_20190711_121402"]]
    # folders = [os.path.join(PARENT_DIR, file) for file in ['21RR060004-A-12-01_HE-STAIN_20210825_161001', '19RR060020-A-07-01_HE-STAIN_20190711_004017', '18rr060026-a-24-01_he-stain_20180301_113449']]
    # folders = [os.path.join(PARENT_DIR, file) for file in ['19RR000008-A-62-01_HE-STAIN_20190704_143754']]
    exclude = [os.path.join(PARENT_DIR, file) for file in ['19RR060061-A-10-01_HE-STAIN_20191014_162043', '19RR000008-A-62-01_HE-STAIN_20190704_143754']]
    folders = [os.path.abspath(os.path.join(PARENT_DIR, p)) for p in os.listdir(PARENT_DIR) if p!= '.DS_Store' and not p.endswith('.csv') and p!= 'unwanted']
    for folder in folders[16:]:
        if folder in exclude:
            continue
        else:
            split_to_groups(folder)
            copy_to_merge(folder)
            color_code(folder)
            rename_all(folder)
