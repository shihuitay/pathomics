import os
import torch
import torch.nn as nn
from torchvision import models
import torchvision.models as models

device=torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')


def get_children(model: torch.nn.Module):
    children = list(model.children())
    flatt_children = []
    if children == []:
        return model
    else:
       # look for children from children... to the last child!
       for child in children:
            try:
                flatt_children.extend(get_children(child))
            except TypeError:
                flatt_children.append(get_children(child))
    return flatt_children

vgg = models.vgg16(weights=None)
vgg = vgg.to(device)
base_conv = nn.Sequential(*list(vgg.children())[:-1])


class VGG16(nn.Module):
    def __init__(self):
        super(VGG16, self).__init__()
        self.custom_model = base_conv
        self.flatten = nn.Flatten()
        # self.avgPool = nn.AdaptiveAvgPool2d((1,1))
        self.dropout = nn.Dropout(p=0.4)
        self.linear = nn.Linear(25088,1)
        self.sigmoid = nn.Sigmoid()
        

    def forward(self, x):
        x = self.custom_model(x)
        x = self.dropout(x)
        x = self.flatten(x)
        logits = self.linear(x)
        return logits
    



    




