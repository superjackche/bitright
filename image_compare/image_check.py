import numpy as np
from PIL import Image
from image_match.goldberg import ImageSignature


def calc_accuracy(path1, path2):
    gis = ImageSignature()
    # Keep Goldberg's signature algorithm; bypass its obsolete image loader.
    with Image.open(path1) as image:
        a = gis.generate_signature(np.asarray(image.convert('RGB')))
    with Image.open(path2) as image:
        b = gis.generate_signature(np.asarray(image.convert('RGB')))
    return gis.normalized_distance(a, b)
