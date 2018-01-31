import cv2
import numpy as np
import logging

class ImageAligner:
    def __init__(self):
        pass

    def find_transformation_to_upscaled_reference(self, image_reference, image, scale_factor):
        """

        :param image_reference:
        :type image_reference: :class:`~src.image.Image`
        :param image:
        :type image: :class:`~src.image.Image`
        :return:
        """
        image_reference_scaled = image_reference.scale(scale_factor)

        return self.find_transformation(image_reference_scaled, image)

    def find_transformation(self, image_reference, image):
        """

        :param image_reference:
        :type image_reference: :class:`~src.image.Image`
        :param image:
        :type image: :class:`~src.image.Image`
        :return:
        """
        # todo: see comment
        # images can have different size. make finding the transformation easier by prescalig
        # get the scale factor between the images
        scale_factor = self.get_scale_factor_between_images(image_reference, image)

        ### the transformation matrix to upscale and align the image to reference is to be obtained.
        # because the scale factor cannot be feeded to estimaterigidtransform directly, the image is scaled up
        # for estimaterigidtransform, which yields the transform matrix between the upscaled.
        # then, the initial matrix for ecc is constructed by chaining a matrix that scales by scale factor
        # with the resulted matrix

        # upscale image to reference
        image_scaled = image.scale(scale_factor)

        # rough inital alignment using feature detection
        warp_matrix_upscaled_image_to_reference = cv2.estimateRigidTransform(image_reference.data,
                                                                             image_scaled.data,
                                                                             fullAffine=False)

        # create initial matrix
        warp_matrix_scale = np.eye(2, 3, dtype=np.float32) * scale_factor
        initial_warp_matrix = self.concatenate_affine_transformations(warp_matrix_scale,
                                                                      warp_matrix_upscaled_image_to_reference)

        # if estimateRigidTransform has failed, create unity matrix
        if initial_warp_matrix is None:
            logging.warning("Initial alignment failed!")
            warp_matrix = np.eye(2, 3, dtype=np.float32)

        # @todo: those two parameters can be set in config!
        # Specify the ECC criteria
        number_of_iterations = 500
        termination_eps = 1e-5
        criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
                    number_of_iterations, termination_eps)

        # etc needs greyscale images
        image_reference_grey = image_reference.get_image_as_greyscale()
        image_grey = image.get_image_as_greyscale()



        # Run the ECC algorithm. The results are stored in warp_matrix.
        try:
            (cc, transform_matrix) = cv2.findTransformECC(image_grey.data.astype(np.float32),
                                                          image_reference_grey.data.astype(np.float32),
                                                          initial_warp_matrix.astype(np.float32),
                                                          motionType=cv2.MOTION_AFFINE,
                                                          criteria=criteria)
        except:
            raise ValueError("Cannot align the image via ECC")

        image.transform_matrix = transform_matrix

    def get_scale_factor_between_images(self, image_reference, image):
        """ Get scale factor to scale image to image_reference

        :param image_reference:
        :type image_reference: :class:`~src.image.Image`
        :param image:
        :type image: :class:`~src.image.Image`
        :return:
        """

        return image_reference.diagonal_resolution / image.diagonal_resolution

    def concatenate_affine_transformations(self, matrix_1, matrix_2):
        """ Concatenate 2 OpenCV affine transfromations to a new transformation corresponding to the chaining
            matrix_1 -> matrix_2

        :param matrix_1:
        :param matrix_2:
        :return: combined affine matrix
        """

        # todo: correct that way?
        # See https://stackoverflow.com/questions/13557066/built-in-function-to-combine-affine-transforms-in-opencv

        # two 3x3 eye matrices
        temp_1, temp_2 = np.eye(3), np.eye(3)

        # fill matrices into top part of temporary matrices
        temp_1[:2] = matrix_1
        temp_2[:2] = matrix_2

        # multiply temporary matrices. result is the top part, containing new matrix
        result = np.dot(temp_2, temp_1)[:2]

        return result