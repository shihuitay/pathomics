import os
import shutil
import random

good_folder = "/Users/shihuitay/Desktop/pathomics/model/data/good"
bad_folder = "/Users/shihuitay/Desktop/pathomics/model/data/bad"

# Define paths for the train, validation, and test folders
train_folder = "/Users/shihuitay/Desktop/pathomics/model/data/train"
val_folder = "/Users/shihuitay/Desktop/pathomics/model/data/val"
test_folder = "/Users/shihuitay/Desktop/pathomics/model/data/test"

# Create train, val, and test folders if they don't exist
for folder in [train_folder, val_folder, test_folder]:
    os.makedirs(folder, exist_ok=True)

# Function to copy images to destination folder
def copy_images(image_paths, dest_folder):
    for img_path in image_paths:
        img_name = os.path.basename(img_path)
        shutil.copy(img_path, os.path.join(dest_folder, img_name))

# Get list of "good" and "bad" image paths
good_images = [os.path.join(good_folder, img) for img in os.listdir(good_folder)]
bad_images = [os.path.join(bad_folder, img) for img in os.listdir(bad_folder)]

# Shuffle the image lists
random.shuffle(good_images)
random.shuffle(bad_images)

for folder in [train_folder, val_folder, test_folder]:
    os.makedirs(os.path.join(folder, '0good'), exist_ok=True)
    os.makedirs(os.path.join(folder, '1bad'), exist_ok=True)

# Split the shuffled lists into train, val, and test sets
train_good = good_images[:int(0.7 * len(good_images))]
val_good = good_images[int(0.7 * len(good_images)):int(0.8 * len(good_images))]
test_good = good_images[int(0.8 * len(good_images)):]

train_bad = bad_images[:int(0.7 * len(bad_images))]
val_bad = bad_images[int(0.7 * len(bad_images)):int(0.8 * len(bad_images))]
test_bad = bad_images[int(0.8 * len(bad_images)):]





if __name__ == '__main__':
    copy_images(train_good, os.path.join(train_folder, '0good'))
    copy_images(val_good, os.path.join(val_folder, '0good'))
    copy_images(test_good, os.path.join(test_folder, '0good'))

    copy_images(train_bad, os.path.join(train_folder, '1bad'))
    copy_images(val_bad, os.path.join(val_folder, '1bad'))
    copy_images(test_bad, os.path.join(test_folder, '1bad'))