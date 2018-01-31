from src.image_aligner import ImageAligner
from src.gradient_descend_super_resolution import SuperResolution3D

class Upscaler:
    def __init__(self, output_dir_monitoring=None,
                 num_iterations = 100):
        self.num_iterations = num_iterations
        self.output_dir_monitoring = output_dir_monitoring

    def start_upscale(self, images, scale_factor):
        # first image is reference image
        image_reference = images[0]

        # align the images
        aligner = ImageAligner()
        for image in images:
            aligner.find_transformation_to_upscaled_reference(image_reference, image, scale_factor)

        # perform super resolution
        # todo: prior!
        gradient_descender = SuperResolution3D(learning_rate=1.,
                                               prior=None)
        image_upscaled = gradient_descender.start_optimization(num_iterations=self.num_iterations,
                                                               images=images,
                                                               scale_factor=scale_factor)

        return image_upscaled