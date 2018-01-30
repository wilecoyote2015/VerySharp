import collections
import scipy.signal
import numpy as np
from copy import deepcopy, copy
from src.data_holders.image import ImageHdu2D, ImageHduDatacube
import cv2

# todo: irgendwie wird das bild mit der falschen groesse eingelesen...

# todo: some way to handle locally variable PSFs

# todo: implement transposed option

# todo: most kernels are available in astropy.
# analog to lsf, create an interface for astropy psfs.

# todo: no own classes for derivatives. better, provide a function in base that calculates the derivative
# for all parameters numerically.
# use scipy.misc.derivative for this for every pixel of the kernel
# the psf-finder and the psf-calculator between images must be updated accordingly.
# maybe we should drop or modify te support for variable psfs: generate kernel pixel-wise from the function
# and then convolve only the according slice and insert the center pixe of the result into the result array.
# so, this is done like in the lsf...
# todo: this is IMPORTANT in the future in order to prevent having to perform sub-pixel integration manually.

# todo: in fact, we need sub-pixel integration to be precise.
# maybe, it is really the best to rewrite the class completely so that all the kernel generation is performed
# by external libs like astropy and the derivatives are created numerically (see comment above)
from src.image import Image
class PSFBase:
    def __init__(self, used_coordinates, is_variable=False, parameters=None):
        """
            It is important to use the order the image data is stored with.
        :param is_variable:
        """
        self.parameters = parameters

    def convolve_image(self, image, parameters=None, transposed=False):
        """

        :param image:
        :type image:  :class:`~src.image.Image`
        :param parameters:
        :param transposed:
        :return:
        """
        if parameters is None:
            parameters = self.parameters

        image_data_convolved = self.convolve_image_data(image.data, parameters, transposed)
        image_convolved = image.create_image_copy(image_data=image_data_convolved)

        return image_convolved

    def convolve_image_data(self, image_data, parameters=None, transposed=False):
        """

        :param image_data: Data from an image
        :type image_data: np.ndarray
        :param parameters: dict with the parametes
        :type parameters: dict
        :return:
        """

        if parameters is None:
            parameters = self.parameters

        kernel = self.get_kernel_as_array_auto_size(parameters)
        if transposed:
            kernel = np.transpose(kernel)

        try:
            data_convolved = cv2.filter2D(image_data, -1, kernel, borderType=cv2.BORDER_REFLECT)
        except:
            raise ValueError("Convolution failed. Maybe parameters are negative. Paraeters: {}".format(parameters))

        return data_convolved

    def evaluate_for_coordinates(self, coordinates, parameters, coordinates_image=None):
        """ Get the value of the PSF at given coordinates in PSF space, with option to provide coordinates in image
        for which the psf is calculated if it is variable across the image.
        Essentially, this is the PSF function.

        IMPORTANT: Must work with numpy-arrays as coordinates!


        :param coordinates: dict with the coordinates
        :param coordinates_image: Coordinates in image space for which the psf is evaluated.
            Can be None if PSF is invariable over image.
            Is used for variable PSF.
        :param parameters: dict with the parametes
        :type parameters: dict
        :return: value at coordinates
        """
        pass

    def get_kernel_as_array_auto_size(self, parameters=None, coordinates_image=None):
        shape_kernel = self.calc_kernel_shape_from_parameters(parameters)
        return self.get_kernel_as_array(parameters=parameters, shape_kernel=shape_kernel,
                                        coordinates_image=coordinates_image)

    def calc_kernel_shape_from_parameters(self, parameters=None):
        """ calculate the minimal kernel shape to contain relevant values of psf.

        :param parameters:
        :return:
        """
        # todo!
        if parameters is None:
            parameters = self.parameters

        size = np.round(parameters["sigma"] * 7).astype(int)

        # kernel size must be odd. thus, add 1 if it isn't
        if size % 2 == 0:
            size += 1

        return (size, size)


    def get_kernel_as_array(self, shape_kernel, parameters=None, coordinates_image=None):
        """

        :param parameters:
        :param shape_kernel:
        :param coordinates_image:
        :return: kernel as ndarray
        :rtype np.ndarray:
        """

        if parameters is None:
            parameters = self.parameters

        # convert shape to array to make calculations with numpy more convenient
        shape_kernel = np.asarray(shape_kernel)

        # check kernel size
        for kernel_size_dimension in shape_kernel:
            if kernel_size_dimension % 2 == 0:
                raise ValueError("Kernel size must be odd in all components, is {}".format(shape_kernel))

        # get list of sequences of kernel coordinates for each axis to create meshgrid
        kernel_radius = ((shape_kernel - 1) / 2).astype(np.int)
        kernel_coordinates_for_grid = [np.arange(-kernel_radius[i], kernel_radius[i] + 1)
                                       for i in range(len(shape_kernel))]

        # for n-d kernel, creates n ND-arrays, holding coordinates for iteration over the given dimension.
        list_coordinate_dicts = np.meshgrid(*kernel_coordinates_for_grid)
        dict_coordinate_grids = self.create_coordinate_element_dict_from_list(['x', 'y'], list_coordinate_dicts)

        kernel = self.evaluate_for_coordinates(dict_coordinate_grids, parameters)

        return kernel

    def create_coordinate_element_dict_from_list(self, coordinate_names, list_elements):
        dict_elements = {name_coordinate:grid for name_coordinate, grid in zip(coordinate_names,
                                                                                        list_elements)}

        return dict_elements

class PSFGaussian2DSymmetric(PSFBase):
    def __init__(self, parameters=None):
        PSFBase.__init__(self, used_coordinates=['y', 'x'], parameters=parameters)

    def evaluate_for_coordinates(self, coordinates, parameters, coordinates_image=None):
        """ Get the value of the PSF at given coordinates in PSF space, with option to provide coordinates in image
        for which the psf is calculated if it is variable across the image.
        Essentially, this is the PSF function.

        IMPORTANT: Must work with numpy-arrays as coordinates!


        :param coordinates: dict with the coordinates
        :param coordinates_image: Coordinates in image space for which the psf is evaluated.
            Can be None if PSF is invariable over image.
            Is used for variable PSF.
        :param parameters: dict with the parametes
        :type parameters: dict
        :return: value at coordinates
        """
        sigma = parameters["sigma"]
        x = coordinates["x"]
        y = coordinates["y"]
        # if sigma is 0, it is delta function, so only center pixel is 1
        if sigma > 0:
            sigma = parameters["sigma"]
            factor = 1 / (sigma**2 * 2 * np.pi)
            exp = np.exp(- (x**2 + y**2) / (2 * sigma**2))

            return factor * exp

        else:
            if x == 0 and y ==0:
                return 1
            else:
                return 0



class PSFGaussian2DSymmetricDerivativeSigma(PSFBase):
    def __init__(self, parameters=None):
        PSFBase.__init__(self, used_coordinates=["y", "x"], parameters=parameters)

    def evaluate_for_coordinates(self, coordinates, parameters, coordinates_image=None):
        """ Get the value of the PSF at given coordinates in PSF space, with option to provide coordinates in image
        for which the psf is calculated if it is variable across the image.
        Essentially, this is the PSF function.

        IMPORTANT: Must work with numpy-arrays as coordinates!


        :param coordinates: dict with the coordinates
        :param coordinates_image: Coordinates in image space for which the psf is evaluated.
            Can be None if PSF is invariable over image.
            Is used for variable PSF.
        :param parameters: dict with the parametes
        :type parameters: dict
        :return: value at coordinates
        """

        x = coordinates["x"]
        y = coordinates["y"]
        sigma = parameters["sigma"]
        factor_1 = (x**2 + y**2) / (sigma**5 * 2 * np.pi)
        factor_2 = 1/(sigma**3 * np.pi)
        exp = np.exp(- (x**2 + y**2) / (2 * sigma**2))

        return (factor_1 - factor_2) * exp

class PSFDelta2D(PSFBase):
    def __init__(self, parameters=None):
        PSFBase.__init__(self, used_coordinates=["y", "x"], parameters=parameters)

    def evaluate_for_coordinates(self, coordinates, parameters, coordinates_image=None):
        """ Get the value of the PSF at given coordinates in PSF space, with option to provide coordinates in image
        for which the psf is calculated if it is variable across the image.
        Essentially, this is the PSF function.

        IMPORTANT: Must work with numpy-arrays as coordinates!


        :param coordinates: dict with the coordinates
        :param coordinates_image: Coordinates in image space for which the psf is evaluated.
            Can be None if PSF is invariable over image.
            Is used for variable PSF.
        :param parameters: dict with the parametes
        :type parameters: dict
        :return: value at coordinates
        """

        return 1. if coordinates["x"] == 0 and coordinates["y"] == 0 else 0  # todo: maybe almost equal must be used

class PSFDummy2D(PSFBase):
    def __init__(self, parameters=None):
        PSFBase.__init__(self, used_coordinates=["y", "x"], parameters=parameters)

    def convolve_image_data(self, image_data, parameters=None, transposed=False):
        return image_data