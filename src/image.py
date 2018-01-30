import cv2
import numpy as np
from copy import deepcopy

class Image:
    def __init__(self, filepath=None, image_data=None, transform_matrix=None, warp_map=None, name=None, psf=None):
        if filepath is None and image_data is None:
            raise ValueError("Either filepath or Data must be given")

        if filepath is not None:
            self.filepath = filepath
            self.image_data = None
        else:
            self.image_data = image_data
            self.filepath = None

        self.transform_matrix = transform_matrix
        self.warp_map = warp_map
        self.name=name
        self.psf = psf

    @property
    def data(self):
        """ Get data. Axes have order: x, y, chroma

        :return:
        """
        if self.filepath is not None:
            data = cv2.imread(self.filepath)

        elif self.image_data is not None:
            data = self.image_data
        else:
            raise ValueError("Image has neither filepath nor data")

        return data

    @property
    def shape(self):
        return self.data.shape

    @property
    def spatial_resolution(self):
        return {"x": self.data.shape[0],
                "y": self.data.shape[1]}

    @property
    def num_colors(self):
        shape = self.shape
        if len(shape) == 2:
            return 1
        else:
            return shape[2]

    def scale(self, scale_factor, interpolation='bicubic'):
        if interpolation == 'bicubic':
            interpolation_cv2 = cv2.INTER_CUBIC
        elif interpolation == 'lanczos':
            interpolation_cv2 = cv2.INTER_LANCZOS4
        elif interpolation == 'area':
            interpolation_cv2 = cv2.INTER_AREA
        else:
            raise ValueError("Interpolation {} is not supported. Allowed: bicubic, lanczos".format(interpolation))

        # flip because opencv needs the shape as width, height. incredible...
        resolution_current = self.spatial_resolution
        shape_new = (np.round(resolution_current['x'] * scale_factor),
                     np.round(resolution_current['y'] * scale_factor))
        data_scaled = cv2.resize(self.data, dsize=shape_new, interpolation=interpolation_cv2)

        return self.create_image_copy(image_data=data_scaled,
                                      transform_matrix=None,
                                      warp_map=None)

    def transform(self, transform_matrix, resolution_x, resolution_y, inverse=False,
                  border_value=0):
        if inverse:
            transform_matrix = cv2.invertAffineTransform(transform_matrix)

        image_data_aligned = cv2.warpAffine(self.data, transform_matrix,
                                            (resolution_x, resolution_y),
                                            borderMode=cv2.BORDER_CONSTANT,
                                            borderValue=border_value)

        return self.create_image_copy(image_data=image_data_aligned,
                                      transform_matrix=None,
                                      warp_map=None)

    def warp(self):
        raise NotImplementedError
        # todo

    def get_image_as_greyscale(self):
        if self.num_colors == 1:
            return self.create_image_copy()
        else:
            data_greyscale = cv2.cvtColor(self.data, cv2.COLOR_RGB2GRAY)
            return self.create_image_copy(image_data=data_greyscale)

    def create_image_copy(self, **kwargs):
            # todo: better create a deepcopy of the hdu? but this doesnt work, right?...
            arguments_to_pass = {"image_data": deepcopy(self.data),
                                 "filepath": deepcopy(self.filepath),
                                 "warp_map": deepcopy(self.warp_map),
                                 "transform_matrix": deepcopy(self.transform_matrix),
                                 "name": deepcopy(self.name),
                                 "psf": deepcopy(self.psf)}

            # if data or filepath is given, do not overtake the other from current image
            if "data" in kwargs and kwargs["image_data"] is not None:
                arguments_to_pass.pop("filepath")
            elif "filepath" in kwargs and kwargs["filepath"] is not None:
                arguments_to_pass.pop("image_data")


            # overwrite given parameters
            for key_argument in arguments_to_pass:
                if key_argument in kwargs and kwargs[key_argument] is not None:
                    arguments_to_pass[key_argument] = kwargs[key_argument]

            return Image(**arguments_to_pass)

    def save_as_image(self, filepath):
        cv2.imwrite(filepath, self.data)