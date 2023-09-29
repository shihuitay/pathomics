'''this file has to be executed in pyvips-env'''
import os
os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib/'
import pyvips
import re
import time
import multiprocessing
import gc
from glob import glob
import sys

def sort_key(filename):
    match = re.match(r"(\d+)_(\d+)\.jpg", filename)
    if match:
        return int(match.group(2)), int(match.group(1))
    return filename

def merge(folder:str):
    tile_folder = os.path.join(folder, 'merge')
    output_filename = f'color_{os.path.basename(folder)}'
    output_path = os.path.join(folder, output_filename)
    filenames = [file for file in os.listdir(tile_folder) if file.endswith('.jpg')]
    unique_x_values = set()
    for item in filenames:
        x_value = int(item.split('_')[0])
        unique_x_values.add(x_value)
    cols = len(unique_x_values)
    sorted_filenames = sorted(filenames, key=sort_key)
    latest =[]
    for filename in sorted_filenames:
        new = os.path.join(folder, 'merge', filename)
        latest.append(new)
    images = [pyvips.Image.new_from_file(filename, access="sequential") for filename in latest]
    joined = pyvips.Image.arrayjoin(images, across=cols)
    joined.tiffsave(output_path, tile=False, compression="jpeg", pyramid=True)
    print(f'Done: {folder}')



# if __name__ == '__main__':
#     PARENT_DIR = '/Users/shihuitay/Desktop/pathomics/data/250'
#     folders = glob(PARENT_DIR + "/*/")
#     st = time.time()
#     try:
#         pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
#         pool.map(merge, folders)
#         pool.close()
#         pool.join()
#         et = time.time()
#         print('Execution time:', et - st, 'seconds')
#     except KeyboardInterrupt:
#         print("Main process received KeyboardInterrupt")
#         if 'pool' in locals():
#             pool.terminate()
#             pool.join()
#         gc.collect(1) 
#         sys.exit(1)


if __name__ == '__main__':
    PARENT_DIR = '/Users/shihuitay/Desktop/pathomics/data/250'
    # folders = [os.path.join(PARENT_DIR, p) for p in os.listdir(PARENT_DIR) if os.path.isdir(os.path.join(PARENT_DIR, p))]
    folders = [os.path.join(PARENT_DIR, file) for file in ['19RR000008-A-42-01_HE-STAIN_20190703_173035', '19RR060020-A-07-01_HE-STAIN_20190711_004017']]
    for folder in folders:
        merge(folder)
