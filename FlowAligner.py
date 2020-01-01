import cv2
import rawpy
import numpy as np
from tqdm import tqdm

import logging

# todo: perform alignment for mosaiced raw

class Dataset:
    def __init__(self, image_raw=None, map_flow=None):
        # libraw raw image
        self.image_raw = image_raw

        # optical flow relative to reference image
        self.map_flow = map_flow

    def image_rgb(self, colorspace=rawpy.ColorSpace.sRGB):
        # demosaic image with libraw
        # do not apply white balance
    
        params = rawpy.Params(
            user_wb=(1, 1, 1, 1),
            # use_camera_wb=True,
            gamma=(1, 1),
            output_color=colorspace,
            output_bps=16,
            half_size=True  # todo: testing
        )
    
        result = (self.image_raw.postprocess(
            params
        ) / 2**16).astype(np.float32)
        return result
        
        
        # result = (self.image_raw.postprocess(
        #     user_wb=(1,1,1,1),
        #     # use_camera_wb=True,
        #     gamma=(1,1),
        #     output_color=colorspace,
        #     output_bps=16,
        #     half_size=True  # todo: testing
        # ) / 2**16).astype(np.float32)
        # return result

    def image_greyscale(self, **kwargs):
        return cv2.cvtColor(self.image_rgb(**kwargs), cv2.COLOR_RGB2GRAY)

    @property
    def image_raw_data(self):
        return self.image_raw.raw_image_visible
    
    def image_rgb_back_transformed(self, **kwargs):
        # remap needs absolute coordinates for each pixel instead of shifts. Hence, construct this.
        # todo: this is not the back trahsform!?
        image = self.image_rgb(**kwargs)
        return self.transform_image(image)

    
    def transform_image(self, image):
        distortion_map = self.convertOpticalFlowToDistortionMap(self.map_flow)
        return np.clip(cv2.remap(image,
                         distortion_map, None, cv2.INTER_CUBIC), 0, 1)


    ## Calculate an OpenCV map that can be used to remap an image according
    #  to the optical flow vector field using OpenCV remap function
    #  @param optical_flow optical flow as numpy array
    #  @param distortion_map OpenCV map as numpy array
    def convertOpticalFlowToDistortionMap(self, optical_flow):
        # get x and y resolution of optical flow (and so also of image)    
        shape_optical_flow = optical_flow.shape[:-1]

        # create empty distortion maps for x and y separately because 
        # opencv remap needs this
        distortion_map_x = np.zeros(shape_optical_flow, np.float32)  # only x and y
        distortion_map_y = np.zeros(shape_optical_flow, np.float32)  # only x and y 

        # fill the distortion maps
        for x in range(shape_optical_flow[1]):
            distortion_map_x[:, x] = optical_flow[:, x, 0] + x
        for y in range(shape_optical_flow[0]):
            distortion_map_y[y] = optical_flow[y, :, 1] + y

        distortion_map = np.rollaxis(np.asarray([distortion_map_x, distortion_map_y]), 0, 3)

        return distortion_map
    
    
    def get_ones_transformed(self):
        ones = np.ones_like(self.image_greyscale())
        return self.transform_image(ones)
        


class FlowAligner:
    def __init__(self):
        pass
    
    def get_flows_images(self, dataset_reference: Dataset, datasets: [Dataset]):
        # reference_greyscale = dataset_reference.image_greyscale
        reference_rgb_int = np.round((
            dataset_reference.image_rgb(colorspace=rawpy.ColorSpace.sRGB) * 255
        )).astype(np.uint8)
        logging.info('Getting flows')
        
        parameters = cv2.optflow.RLOFOpticalFlowParameter_create()
        parameters.setLargeWinSize(60)
        
        pass
        
        for idx, dataset in enumerate(tqdm(datasets)):
            # cv2.imshow('bla', reference_rgb)
            dataset_rgb_int = np.round(dataset.image_rgb(colorspace=rawpy.ColorSpace.sRGB) * 255).astype(np.uint8)
            # cv2.imwrite(f'rgb_int_{idx}.png', (cv2.cvtColor(dataset_rgb_int, cv2.COLOR_RGB2BGR)))

            dataset.map_flow = cv2.optflow.calcOpticalFlowDenseRLOF(
                                                                    reference_rgb_int,
                                                                    dataset_rgb_int,
                                                                    None,
                                                                    rlofParam=parameters,
                                                                    gridStep=(4, 4),
                                                                    interp_type=cv2.optflow.INTERP_GEO,
                                                                    use_variational_refinement=False,
                                                                    forwardBackwardThreshold=0.01,
                                                                    use_post_proc=True
                                                                    )


            # dataset_grey = cv2.cvtColor(dataset_rgb_int, cv2.COLOR_RGB2GRAY)
            # reference_grey = cv2.cvtColor(reference_rgb_int, cv2.COLOR_RGB2GRAY)
            # dataset.map_flow = cv2.calcOpticalFlowFarneback(reference_grey, dataset_grey, None, 0.5, 3, 15, 3, 5, 1.2, 0)

            # save flow images
            mag, ang = cv2.cartToPolar(dataset.map_flow[..., 0], dataset.map_flow[..., 1])
            hsv = np.zeros_like(dataset_rgb_int)
            hsv[..., 1] = 255
            hsv[..., 0] = ang * 180 / np.pi / 2
            hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
            bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
            
            cv2.imwrite(f'flow_{idx}.png', bgr)

            # cv2.imwrite(f'Transformed_{idx}.png', np.round((cv2.cvtColor(dataset.image_rgb_back_transformed(), cv2.COLOR_RGB2BGR) * (2 ** 8 - 1))).astype(np.int))

    def stack_images_rgb(self, dataset_reference, datasets):
        # 
        # for idx, dataset in enumerate([dataset_reference] + datasets):
        #     cv2.imwrite(f'Ref{idx}.png',
        #                 (cv2.cvtColor(dataset.image_rgb(), cv2.COLOR_RGB2BGR) * 2**16).astype(np.uint16))

        # obtain flows for all images
        self.get_flows_images(dataset_reference, datasets)
        
        num_stacked_per_pixel = np.ones_like(dataset_reference.image_greyscale())
        
        # remap images
        result = np.copy(dataset_reference.image_rgb())
        logging.info('Remapping Images')
        for dataset in tqdm(datasets):
            result += dataset.image_rgb_back_transformed()
            num_stacked_per_pixel += dataset.get_ones_transformed()

        num_stacked_per_pixel = np.tile(np.expand_dims(num_stacked_per_pixel, 2), (1, 1, 3))

        return result / num_stacked_per_pixel
    
if __name__ == "__main__":
    paths_images = [
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0494.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0495.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0496.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0497.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0498.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0499.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0500.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0500.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0501.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0502.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0503.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0504.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0505.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0506.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0507.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0508.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0509.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0510.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0511.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0512.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0513.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0514.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0515.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0517.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0518.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0519.RAF',
        '/run/media/bjoern/daten/Programming/VerySharp/flow_test/s/DSCF0520.RAF',
    ]

    images = [Dataset(image_raw=rawpy.imread(path)) for path in paths_images[1:]]
    image_reference = Dataset(image_raw=rawpy.imread(paths_images[0]))

    aligner = FlowAligner()

    img = aligner.stack_images_rgb(image_reference, images)
    
    cv2.imwrite('Res.png', np.round(cv2.cvtColor(img, cv2.COLOR_RGB2BGR) * (2**16)).astype(np.uint16))

    pass