import os
os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib/'
import sys
sys.path.append('/Users/shihuitay/Desktop/pathomics/filtering')
sys.path.append('/Users/shihuitay/Desktop/pathomics/utils')
import cv2
import matplotlib.pyplot as plt
import numpy as np
from openslide import open_slide
import shutil
from glob import glob
import uuid
import json
import csv
import time
import multiprocessing
import gc
from openslide.deepzoom import DeepZoomGenerator
from filtering import remove_blank, remove_rbc, remove_pen, remove_fold

class WSI_Pipeline:
    def __init__(self, filepath: str, tile_size: int=None):
        '''filepath: filepath of the cropped whole slide image'''
        '''set the desired tile size if wsi hasn't been processed'''
        self.parent_dir = os.getcwd()
        self.blank = 0
        self.pen = 0
        self.blur = 0
        self.rbc = 0
        self.fold = 0 
        self.filtered = 0
        if tile_size is not None:
            self.filename = os.path.basename(filepath).split('.')[0]
            self.tile_dir = os.path.join(self.parent_dir, 'data', str(tile_size), self.filename)
            self.slide = open_slide(filepath)
            self.tiles = DeepZoomGenerator(self.slide, tile_size=tile_size, overlap=0,limit_bounds=False)
            os.makedirs(self.tile_dir, exist_ok=True)
            self.save_tiles(self.tiles, self.tile_dir)
            self.csv = os.path.join(self.parent_dir, 'data', str(tile_size),"output.csv")
        else:
            if os.path.isdir(filepath):
                self.filename = os.path.basename(filepath)
                self.tile_dir = filepath
                self.tile_num = len([file for file in os.listdir(self.tile_dir) if file.endswith(('.png', '.tif'))])
                self.csv = os.path.join(self.parent_dir, 'data', os.path.dirname(filepath),"output.csv")

    def save_tiles(self, tiles:object, dest:str):
        '''
        tiles: tiles object generated by DeepZoomGenerator
        dest: directory to save the tiles
        '''
        # print('Started tiling process.........')
        cols, rows = tiles.level_tiles[tiles.level_count -1] # get the final level
        for row in range(rows):
            for col in range(cols):
                tile_name = os.path.join(dest, '%d_%d'%(col,row))
                temp_tile = np.array(tiles.get_tile(tiles.level_count -1, (col, row)).convert('RGB'))
                plt.imsave(tile_name + ".png", temp_tile)
        # print(f'Number of tiles saved for {self.filename}: ', self.tiles.tile_count)
        self.tile_num = self.tiles.tile_count

    def filter(self):
        # print('Started filtering process..........')
        filepaths = glob(os.path.join(self.tile_dir, '*.png'))
        os.makedirs(os.path.join(self.tile_dir, 'blank'), exist_ok=True)
        os.makedirs(os.path.join(self.tile_dir, 'rbc'), exist_ok=True)
        os.makedirs(os.path.join(self.tile_dir, 'pen'), exist_ok=True)
        os.makedirs(os.path.join(self.tile_dir, 'fold'), exist_ok=True)
        blank = os.path.join(self.tile_dir, 'blank')
        rbc = os.path.join(self.tile_dir, 'rbc')
        pen = os.path.join(self.tile_dir, 'pen')
        fold = os.path.join(self.tile_dir, 'fold')
        model_path = '/Users/shihuitay/Desktop/pathomics/model/models/new/2023-09-14(final)/epoch_19.pth'
        
        for filepath in filepaths:
            img = cv2.imread(filepath)
            if remove_blank(img, 30): #20
                shutil.move(filepath, os.path.join(blank, os.path.basename(filepath)))
                self.blank += 1
                continue
            
            if remove_pen(img, thres=10):
                shutil.move(filepath, os.path.join(pen, os.path.basename(filepath)))
                self.pen += 1
                continue
            
            if remove_rbc(img, thres=20): #3
                shutil.move(filepath, os.path.join(rbc, os.path.basename(filepath)))
                self.rbc += 1
                continue

            if remove_fold(filepath, model_path):
                shutil.move(filepath, os.path.join(fold, os.path.basename(filepath)))
                self.fold += 1

    def get_coor(self, cropped=False):
        '''get the coordinates of the filtered tiles 
        to locate the tiles on WSI in Qupath later
        cropped = whether the original WSI was cropped'''
        filtered =  [entry for entry in os.listdir(self.tile_dir) if entry.endswith(('.png', '.tif'))]
        self.filtered = len(filtered)
        coors = []
        # Qupath requires the objectID to be Universally Unique Identifier
        unique_ids = [str(uuid.uuid4()) for _ in range(len(filtered))]
        if cropped:
            for filename , id_ in zip(filtered, unique_ids):
                parts = filename.split('_')
                c = int(parts[0])
                r = int(parts[1].split('.')[0]) 
                x1 = c * self.tilesize
                x2 = c * self.tilesize + self.tilesize
                y1 = r * self.tilesize
                y2 = r * self.tilesize + self.tilesize
                coor = [[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1,y1]] # clock-wise
                my_dict = {}
                my_dict["filename"] = filename
                my_dict["id"] = id_ 
                my_dict["coor"] = coor
                coors.append(my_dict)
        else:
            for filename , id_ in zip(filtered, unique_ids):
                parts = filename.split('-')
                x1 = int(parts[1])
                y1 = int(parts[3])
                # len_name = len(parts[1])+len(parts[3]) + 6 # + 2 here is used for the 2 a's that will be added later
                w = int(parts[5])
                h = int(parts[7].split('.')[0])
                x2 = x1 + w
                y2 = y1 + h
                coor = [[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1,y1]] # clock-wise
                my_dict = {}
                my_dict["filename"] = filename
                # Qupath requires the objectID to be Universally Unique Identifier; we append the coordinates to the end of the identifier
                # my_dict["id"] = id_[:-len_name] + 'and' + parts[1] + 'and' + parts[3]   # so the coordinates will be the last two numbers separated by 'x0'
                my_dict["id"] = id_
                my_dict["coor"] = coor
                coors.append(my_dict)
        
        # save filename:objectID to csv
        csv_file = os.path.join(self.tile_dir, 'objectID.csv')
        key_to_skip = 'coor'
        with open(csv_file, mode='w', newline='') as file:
            field_names = ['filename', 'id']
            writer = csv.DictWriter(file, fieldnames=field_names)
            writer.writeheader()
            for row in coors:
                writer.writerow({key: value for key, value in row.items() if key != key_to_skip})

        # Create the GeoJSON features
        features = []
        for item in coors:
            feature = {}
            feature["type"] = "Feature"
            feature["id"] = item["id"]
            feature["geometry"]= {
                    "type": "Polygon",
                    "coordinates": [item["coor"]]
                }
            feature["properties"] = {
                    "objectType": "annotation"
                }

            features.append(feature)

        output_file = os.path.join(self.tile_dir,f"{self.filename}.geojson")
        with open(output_file, "w") as f:
            json.dump(features, f, indent=2)
    
    def save_to_csv(self):
        '''record the number of removed files'''
        with open(self.csv, 'a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            # Write the data to the next empty row
            csv_writer.writerow([self.filename, self.tile_num, self.blank, self.pen, self.rbc, self.fold, self.filtered])

def process_file(args):
    if len(args)==2: # filepath to the cropped files and tile size are provided, indicating tiling is needed
        filepath, tile_size, = args 
        pipeline = WSI_Pipeline(filepath, tile_size)
        pipeline.filter()
        pipeline.get_coor(cropped=True)
    else:
        filepath = args
        pipeline = WSI_Pipeline(filepath)
        pipeline.filter()
        pipeline.get_coor()
    pipeline.save_to_csv()
    print(f'Completed: {filepath}')

# if __name__ == '__main__':
#     st = time.time()
#     pipeline = WSI_Pipeline('/Users/shihuitay/Desktop/pathomics/data/cropped/19RR060061-A-10-01_HE-STAIN_20191014_162043.tiff', 250)
#     pipeline.filter()
#     pipeline.get_coor()
#     et = time.time()
#     elapsed_time = et - st
#     print('Execution time:', elapsed_time, 'seconds')

if __name__ == '__main__':
    print('Pipeline started......')
    TILE_SIZE = 250
    parent_dir = os.getcwd()
    directory = f'/Users/shihuitay/Desktop/pathomics/data/{TILE_SIZE}/'
    # filepaths = [os.path.abspath(os.path.join(directory, p)) for p in os.listdir(directory) if p!= '.DS_Store' and not p.endswith('.csv')]
    # filepaths = [os.path.abspath(os.path.join(directory, '/Users/shihuitay/Desktop/pathomics/data/250/19RR060060-A-06-01_HE-STAIN_20191014_141613'))]
    filepaths = [os.path.abspath(os.path.join(directory, '/Users/shihuitay/Desktop/pathomics/data/250/21RR060004-A-12-01_HE-STAIN_20210825_161001'))]
    filepaths = [os.path.abspath(os.path.join(directory, '/Users/shihuitay/Desktop/pathomics/data/250/20RR060012-A-37-01_HE-STAIN_20210219_095858'))]
    csv_path = os.path.join(parent_dir, 'data', str(TILE_SIZE), 'output.csv')
    if not os.path.isfile(csv_path):
        with open(csv_path, 'a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['Filename', 'No. of tiles', 'Blank', 'Pen', 'RBC', 'Fold', 'Remaining tiles'])
    else:
        with open(csv_path, 'a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_file.write('\n')
    st = time.time()
    try:
        pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
        pool.map(process_file, filepaths)
        #Close the Pool to release resources
        pool.close()
        pool.join()
        et = time.time()
        print('Execution time:', et - st, 'seconds')
    except KeyboardInterrupt:
        print("Main process received KeyboardInterrupt")
        # Terminate the multiprocessing pool if running
        if 'pool' in locals():
            pool.terminate()
            pool.join()
        # Release resources and clean up memory
        gc.collect(1) 
        # Exit the program with a non-zero exit code
        sys.exit(1)
    
    
    # if len(sys.argv) > 2:
    #     filepaths = [(os.path.join(sys.argv[2], file), sys.argv[1]) for file in os.listdir(sys.argv[2]) if file.endswith(('ome.tif', 'tiff'))]
    # # sys.argv[2] = '/Users/shihuitay/Desktop/pathomics/data/cropped/'
    # else:
    #     directory = f'/Users/shihuitay/Desktop/pathomics/data/{sys.argv[1]}/'
    #     filepaths = [os.path.abspath(os.path.join(directory, p)) for p in os.listdir(directory)]
    
    # st = time.time()
    # try:
    #     pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    #     pool.map(process_file, filepaths)
        
    #     #Close the Pool to release resources
    #     pool.close()
    #     pool.join()
    #     et = time.time()
    #     print('Execution time:', et - st, 'seconds')
    # except KeyboardInterrupt:
    #     print("Main process received KeyboardInterrupt")

    #     # Terminate the multiprocessing pool if running
    #     if 'pool' in locals():
    #         pool.terminate()
    #         pool.join()

    #     # Release resources and clean up memory
    #     gc.collect(1) 
    #     # Exit the program with a non-zero exit code
    #     sys.exit(1)

    





