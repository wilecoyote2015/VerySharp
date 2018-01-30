import cv2
import numpy as np
import logging

class ImageAligner:
    def __init__(self):
        pass

    def find_transformation(self, image_reference, image):
        """

        :param image_reference:
        :type image_reference: :class:`~src.image.Image`
        :param image:
        :return:
        """
        # images can have different size. make finding the transformation easier by prescalig
        # get the scale factor between the images


        # rough inital alignment using feature detection
        initial_warp_matrix = cv2.estimateRigidTransform(image_reference.data, image.data, fullAffine=False)

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