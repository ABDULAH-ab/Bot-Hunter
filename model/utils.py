import torch
from torch import nn


def sample_mask(index, size):
    mask = torch.zeros(size, dtype=torch.bool)
    mask[list(index)] = True
    return mask


def init_weights(module):
    if isinstance(module, nn.Linear):
        nn.init.xavier_uniform_(module.weight)
        if module.bias is not None:
            nn.init.zeros_(module.bias)