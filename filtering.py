'''
remove blank
remove red blood cells
remove pen marks
remove tissue folds
'''
from PIL import Image
import cv2
import numpy as np
from model import VGG16
import torch
from torchvision import transforms

def calculate_white_percentage(img):
    white_thres = 220
    total_pixels = img.shape[0] * img.shape[1]
    white_pixels = np.sum(np.all(img >= white_thres, axis=-1))
    white_percentage = (white_pixels / total_pixels) * 100
    return white_percentage

def variance_of_laplacian(img):
# compute the Laplacian of the image and then return the focus
    return cv2.Laplacian(img, cv2.CV_64F).var()

def calculate_blur_score(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return laplacian_var

def detect_empty(img, mean_thres=100, std_thres=25):
    'img should be in grayscale'
    edges = cv2.Canny(img, 30, 100) 
    if np.count_nonzero(edges) <500:  # fully/partially empty image would not have many edges
        return True
    else:
        std = np.std(img)
        mean = np.mean(img)
        if mean < mean_thres and std < std_thres:  # to detect greyish blank tiles 
            return True

def remove_blank(img, white_threshold:int):
    'white_threshold: percentage of blank'
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    white_percentage = calculate_white_percentage(img)
    if white_percentage >= white_threshold or detect_empty(gray):
        return True

def remove_rbc(img, thres=20, h_min:int=130, h_max:int=180, s_min:int=110, s_max:int=180):   #thres=2, h_min:int=150, h_max:int=180, s_min:int=150, s_max:int=180
    PINK_MIN = np.array([h_min, s_min, 100],np.uint8)
    PINK_MAX = np.array([h_max, s_max, 255],np.uint8)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hue = hsv[:,:,0]
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]
    mask = np.where((hue>h_min) & (hue < h_max) & (saturation < 150) & (value < 240), 255, 0).astype(np.uint8)
    threshold = cv2.inRange(hsv, PINK_MIN, PINK_MAX)
    final_mask = np.where(mask == 0, threshold, 0)
    pink_pix = np.sum(final_mask==255)
    total_pix = final_mask.shape[0] * final_mask.shape[1]
    percent = pink_pix/total_pix * 100
    if percent>thres:
        return True


# reference: https://github.com/lucasrla/wsi-tile-cleanup/blob/master/wsi_tile_cleanup/filters/pens.py
PENS_RGB = {
    "red": [
        (150, 80, 90),
        (110, 20, 30),
        (185, 65, 105),
        (195, 85, 125),
        (220, 115, 145),
        (125, 40, 70),
        (200, 120, 150),
        (100, 50, 65),
        (85, 25, 45),
    ],
    "green": [
        (150, 160, 140),
        (70, 110, 110),
        (45, 115, 100),
        (30, 75, 60),
        (195, 220, 210),
        (225, 230, 225),
        (170, 210, 200),
        (20, 30, 20),
        (50, 60, 40),
        (30, 50, 35),
        (65, 70, 60),
        (100, 110, 105),
        (165, 180, 180),
        (140, 140, 150),
        (185, 195, 195),
    ],
    "blue": [
        (60, 120, 190),
        (120, 170, 200),
        (120, 170, 200),
        (175, 210, 230),
        (145, 210, 210),
        (37, 95, 160),
        (30, 65, 130),
        (130, 155, 180),
        (40, 35, 85),
        (30, 20, 65),
        (90, 90, 140),
        (60, 60, 120),
        (110, 110, 175),
    ],
}

def remove_pen(img, thres:int=10, pen_color:list=['red', 'blue', 'black']): # might need to adjust the values
    b,g,r = cv2.split(img)
    percent_list = []
    for color in pen_color:
        if color == "red":
            thresholds = PENS_RGB[color]
            t = thresholds[0]
            mask = (r > t[0]) & (g < t[1]) & (b < t[2])

            for t in thresholds[1:]:
                mask = mask | ((r > t[0]) & (g < t[1]) & (b < t[2]))

        elif color == "green":
            thresholds = PENS_RGB[color]
            t = thresholds[0]
            mask = (r < t[0]) & (g > t[1]) & (b > t[2])

            for t in thresholds[1:]:
                mask = mask | (r < t[0]) & (g > t[1]) & (b > t[2])

        elif color == "blue":
            thresholds = PENS_RGB[color]
            t = thresholds[0]
            mask = (r < t[0]) & (g < t[1]) & (b > t[2])

            for t in thresholds[1:]:
                mask = mask | (r < t[0]) & (g < t[1]) & (b > t[2])
        
        elif color == "black":
            t = (120, 120,120) #(100, 100, 100)
            mask = (r < t[0]) & (g < t[1]) & (b < t[2])

        else:
            raise Exception(f"Error: pen_color='{pen_color}' not supported")

        total_pixels = mask.size
        color_pixels = np.sum(mask)
        percent_list.append(color_pixels / total_pixels * 100)

    return any(percent > thres for percent in percent_list)

def remove_fold(file, model_path, device='cpu'):
    model = VGG16()
    state_dict = torch.load(model_path, map_location=device)
    model.load_state_dict(state_dict)
    model.eval()
    model = model.to(device)
    preprocess = transforms.Compose([
                    transforms.Resize((224,224)),
                    transforms.ToTensor(),
                ])
    pil_img = Image.open(file).convert('RGB')
    img_preprocessed = preprocess(pil_img)
    img_preprocessed = img_preprocessed.to(device)
    batch_img_tensor = torch.unsqueeze(img_preprocessed, 0)
    
    with torch.no_grad():
        out = model(batch_img_tensor)
        out_proba = torch.sigmoid(out).cpu().detach().numpy()[0][0]
        out_s = torch.sigmoid(out)
        y_score = out_s.squeeze(-1).cpu().detach().numpy()
        out = out.squeeze(1)>0
        out = out.cpu().detach().numpy()

        if y_score > 0.7:
            return True

def remove_blur(img, thres:int=20):
    blur = calculate_blur_score(img)
    if blur<thres:
        return True
    