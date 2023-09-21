import os
from glob import glob
import shutil
import csv

def count_files(directory:str, target:str):
    '''
    for each WSI, get the number of files removed for targeted category
    directory: parent folder containing the subfolders representing each WSI
    target: targeted folder, e.g., blank
    returns a csv storing the image ID and their respective number of files removed
    '''
    file_dict = {}
    for folder in os.listdir(directory):
        if os.path.isdir(os.path.join(directory, folder)):
            number = len([file for file in os.listdir(os.path.join(directory, folder, target)) if file.endswith('.png')])
            file_dict[folder] = number
    with open(f'{directory}/{target}.csv', 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Filename', target])
        for filename, value in file_dict.items():
            writer.writerow([filename, value])

def undo_filter(directory:str, target:list=None):
    '''
    move all the files in subfolders (blank, rbc, blur, pen, tumor, immune, tumor_immune) to their original folder
    directory: parent folder containing the subfolders representing each WSI
    target: list of folders to be involved, e.g., [blank, rbc]
    '''
    if target is not None:
        for cat in target:
            for root, folders, _ in os.walk(directory):
                for folder in folders:
                    for parent, subfolders, _ in os.walk(os.path.join(root, folder)):
                        for subfolder in subfolders:
                            if subfolder == cat:
                            # Create the full path of the source file
                                files = glob(os.path.join(parent, subfolder, "*.png"))
                                for file in files:
                                    dest = os.path.join(root, folder, os.path.basename(file))
                                    shutil.move(file, dest)
    else: 
        for root, folders, _ in os.walk(directory):
            for folder in folders:
                for parent, subfolders, _ in os.walk(os.path.join(root, folder)):
                    for subfolder in subfolders:
                        if subfolder =='merge':
                            continue
                        files = glob(os.path.join(parent, subfolder, "*.png"))
                        for file in files:
                            dest = os.path.join(root, folder, os.path.basename(file))
                            shutil.move(file, dest)

def delete_file(directory:str, target:str):
    '''
    delete specific file across all folders
    directory: parent folder containing the subfolders representing each WSI
    target: the extension of the files to be deleted
    '''
    for folder in os.listdir(directory):
        to_delete = os.path.join(directory, folder, f'{folder}'+ target)
        if os.path.isfile(to_delete):
            os.remove(to_delete)
            print("remove ", to_delete)

def delete_folder(directory:str, target:str):
    '''
    delete specific folder across all folders
    directory: parent folder containing the subfolders representing each WSI
    target: the name of the folder to be deleted
    '''
    for folder in os.listdir(directory):
        to_delete = os.path.join(directory, folder, target)
        if os.path.isdir(to_delete):
            shutil.rmtree(to_delete)
            print("remove ", to_delete)


if __name__ == '__main__':
    PARENT_DIR = '/Users/shihuitay/Desktop/pathomics/data/250'
    # undo_filter(PARENT_DIR, ['tumor', 'immune', 'tumor_immune'])
    # undo_filter(PARENT_DIR)
    # count_files(PARENT_DIR, 'blank')
    # delete_file(PARENT_DIR, '_new.geojson')
    delete_folder(PARENT_DIR, 'merge')
    


