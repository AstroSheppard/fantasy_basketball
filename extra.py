import numpy as np
from numpy import random

def ev(mean, var):
    mean = mean*3
    return (random.normal(mean, np.sqrt(var), size=100000)>0).sum()/100000
