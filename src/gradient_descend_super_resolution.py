import numpy as np
import logging
from src.image import Image


import os
from matplotlib import pyplot as plt
import copy

class GradientDescentBase:
    def __init__(self, function_to_maximize, function_derivative, learning_rate=1.,
                 output_dir_monitoring=None,
                 decay_momentum=0.9,
                 decay_velocity=0.999,
                 epsilon_adam=1e-8):
        self.output_dir_monitoring = output_dir_monitoring
        self.function_to_maximize = function_to_maximize
        self.function_derivative = function_derivative
        self.learning_rate = learning_rate

        # fix parameters for ADAM descent
        self.decay_momentum = decay_momentum
        self.decay_velocity = decay_velocity
        self.epsilon_adam = epsilon_adam

        self.last_momentum = 0
        self.last_velocity = 0

    def start_optimization(self, num_iterations, initial_value=None, **kwargs):
        """ Function should be overwritten with needed signature.

        :param num_iterations: Number of iterations
        :param initial_value:
        :param kwargs:
        :return:
        """
        return self.perform_optimization(num_iterations, initial_value, **kwargs)

    def perform_optimization(self, num_iterations, initial_value, **kwargs):
        current_value = initial_value

        # reset adam parameters
        self.last_momentum = 0
        self.last_velocity = 0


        # dict with lists for all parameters and "all" for overall residual error
        residual_errors = {}
        for iteration in range(num_iterations):
            logging.info("Performing iteration {} of {}".format(iteration + 1, num_iterations))
            current_value, residual_error = self.perform_optimization_step(current_value, iteration, **kwargs)
            logging.info("Current values: {}".format(current_value))
            logging.info("Residual Error: {}".format(residual_error))


            # adjust learning rate
            # todo: make the adjustment configurable and pass it properly. self.learning rate is only the
            # initial one and should not be altered!
            # todo: can the initial learning rate be adjusted according to image size?
            # todo: the thresholds must be configurable.
            if residual_error is not None:
                if len(residual_errors) > 0:
                    last_residual_error = residual_errors["all"][-1]

                # append the current residual error
                for key, value in residual_error.items():
                    if key not in residual_errors:
                        residual_errors[key] = [value]
                    else:
                        residual_errors[key].append(value)

                if self.output_dir_monitoring is not None:
                    self.plot_residual_errors(residual_errors)

        return current_value

    def plot_residual_errors(self, residual_errors):
        num_residuals = len(residual_errors)
        if num_residuals > 1:
            f, axes = plt.subplots(num_residuals, sharex=True)

            for key_residual, index_residual in zip(residual_errors.keys(), range(num_residuals)):
                axes[index_residual].semilogy(residual_errors[key_residual])
                axes[index_residual].set_title(key_residual)
        else:
            plt.semilogy(residual_errors["all"])
            plt.title("all")

        output_path = os.path.join(self.output_dir_monitoring, "Errors.eps")

        plt.savefig(output_path)
        plt.clf()
        plt.close()

    def perform_adam(self, gradient, current_value, current_iteration):
        # calculate parameters for ADAM
        # timestep is iteration + 1 because current iteration starts at 0, but first time must be 1
        time = current_iteration + 1
        momentum = self.decay_momentum * self.last_momentum + (1 - self.decay_momentum) * gradient
        # must be dtype np.float64 because velocity gets very large.
        velocity = self.decay_velocity * self.last_velocity + (1 - self.decay_velocity) * np.sum(gradient**2,
                                                                                                 dtype=np.float64)

        estimate_momentum = momentum / (1 - self.decay_momentum**time)
        estimate_velocity = velocity / (1 - self.decay_velocity**time)

        # update ADAM parameters
        self.last_momentum = momentum
        self.last_velocity = velocity

        # update the current estimate
        current_value -= self.learning_rate / (np.sqrt(estimate_velocity) + self.epsilon_adam) * estimate_momentum

        return current_value

    def perform_optimization_step(self, current_value, current_iteration, **kwargs):
        pass

    # todo: Denis 2015 beschreiben methoden zur schnellen berechnung der spatial variablen PSF.
    # das sollte hier dann auch implementiert werden.


class SuperResolution3D(GradientDescentBase):
    # todo: The alignment is catastrophic!!!!
    # a look at the alignment monitoring images reveals that there alignment itself does not work well.
    # seems that we really need a better approach here!

    # todo: transforming is done using the transform function of cv2 by now. But, especially for considering the
    # necessity of accurate transposed transformation, maybe it is a good idea to really implement transformation via
    # matrices. CV2 has transformation maps, which are mappings of coordinates. It should be easy to write a function
    # that converts those to a real transformation matrix. It would start with flattening of the matrix with
    # (important!) the flattening function that is used to convert an image to a vector.

    # todo: multiprocessing

    # todo: with every image, only the slice of the datacube that actually corresponds to the filter range of the image
    # should be processed. This can save much processing power! The Datacube class now has a function to get
    # a filter range slice.

    # todo: use mask_valid_pixels of the images if provided, so that gradient is 0 where pixels are invalid
    # will not be that easy due to scaling etc.? This must all be implemented in scaling and transforming things...
    def __init__(self, learning_rate, prior, output_dir_monitoring=None,
                 alternating_descend=False,
                 output_step=10,
                 decay_momentum=0.9,
                 decay_velocity=0.999,
                 epsilon_adam=1e-8):
        self.prior = prior
        self.current_estimate = None,
        GradientDescentBase.__init__(self, function_to_maximize=self.loss_function,
                                     function_derivative=self.gradient_loss_function,
                                     learning_rate=learning_rate,
                                     output_dir_monitoring = output_dir_monitoring,
                                     decay_momentum=decay_momentum,
                                     decay_velocity=decay_velocity,
                                     epsilon_adam=epsilon_adam
                                     )

        self.alternating_descend = alternating_descend
        self.output_step = output_step

    def start_optimization(self, num_iterations, initial_value=None, images=None, scale_factor=None, **kwargs):
        """

        :param num_iterations:
        :param initial_value:
        :type images: list of :class:`~src.image.Image`
        :param kwargs:
        :return:
        """

        # if no initial value is given, use a bicubic upscaled version.
        if initial_value is None:
            initial_value = images[0].scale(scale_factor)

        # save initial estimate
        initial_value.save_as_image(os.path.join(self.output_dir_monitoring, "initial_estimate.png"))

        # Reset parameters for ADAM gradient descent
        self.last_momentum = 0
        self.last_velocity = 0

        # perform the optimization
        return self.perform_optimization(num_iterations, initial_value, images=images)

    def perform_optimization_step(self, current_value, current_iteration, images=None, **kwargs):
        gradient = self.gradient_loss_function(current_value, images)

        # remove infs from gradient, which can occur on border cases
        gradient[np.logical_or(np.isinf(gradient), np.isnan(gradient))] = 0.

        # perform adam
        current_value.data = self.perform_adam(gradient, current_value.data, current_iteration)

        # output the current estimate as image
        # every output_stepth image is written.
        if self.output_dir_monitoring is not None and current_iteration % self.output_step == 0:
            filename = "estimate_{}.png".format(current_iteration)
            filepath = os.path.join(self.output_dir_monitoring, filename)
            current_value.save_as_image(filepath)

        # get the resudal error for printing out and maybe also learning rate adjustments
        residual_error = self.loss_function(images, current_value)

        return current_value, residual_error

    def gradient_loss_function(self, current_value, images):

        gradient = np.zeros_like(current_value.data)
        for image in images:
            logging.info("Calculating log likelihood gradient for image {}".format(image.name))
            gradient += self.gradient_log_likelihood(image, current_value)
            # return gradient_rest
        gradient += self.prior.gradient_log(current_value)

        return gradient

    def gradient_log_likelihood(self, image, current_estimate):
        # calculate residuum. it has the size of the image.
        # if image is 2d, residuum is 2d, too. for datacube, it is 3d.
        residuum = self.calculate_residuum(image, current_estimate)
        image_transposed_generation = self.apply_transposed_generation_matrix(residuum, image, current_estimate)

        return -1 * image_transposed_generation.data

    def apply_transposed_generation_matrix(self, residuum, image, current_estimate):
        """ Apply the transposed form of the generative Matrix Z to residuum

        :param image:
        :return:
        """

        # re-transform residuum by transforming with matrix of image forwards
        # this is equivalent to the transposed transform matrix in W in formula.
        # todo: is this really equivalent? I don't think so!
        # could it be sufficient to not scale the flux to make it right? Just a guess...

        residuum_scaled_to_estimate_size = residuum.transform(image.transform_matrix,
                                                               current_estimate.spatial_resolution["x"],
                                                               current_estimate.spatial_resolution["y"],
                                                               inverse=False)

        residuum_scaled_convolved = image.psf.convolve_image(residuum_scaled_to_estimate_size, transposed=True)

        return residuum_scaled_convolved

    def loss_function(self, images, current_estimate):
        errors = {}
        sum_log_likelihoods = 0.
        for image in images:
            log_likelihood_image = self.log_likelihood_image(image, current_estimate)

            errors[image.name] = - log_likelihood_image

            sum_log_likelihoods += log_likelihood_image
        log_likelihood_prior = np.log(self.prior.prior_image(current_estimate))
        errors["prior"] = - log_likelihood_prior
        sum_log_likelihoods += log_likelihood_prior

        errors["all"] = - sum_log_likelihoods

        return errors

    def log_likelihood_image(self, image, current_estimate):
        # todo: calculate correct likelihood also if likelihood with variance is used!
        residuum = self.calculate_residuum(image, current_estimate)

        # fix undefined values
        residuum.data[np.logical_or(np.isnan(residuum.data), np.isinf(residuum.data))] = 0.

        return image.num_pixels / 2 * np.log(2 / np.pi) - np.sum(residuum.data**2) / 2.

    def calculate_residuum(self, image, current_estimate):
        estimate_blurred = image.psf.convolve_image(current_estimate)

        estimate_blurred_transformed = estimate_blurred.transform(image.transform_matrix,
                                                               image.resolution["x"],
                                                               image.resolution["y"],
                                                               inverse=True,
                                                               border_value=np.nan)

        # borders from transformation where image exceeds field of view of estimate are None.
        # thus, residuum should be 0 at the borders.
        # also, residuum should be 0 where mask_valid_pixels of image is False.
        residuum = np.zeros_like(image.data)

        residuum_valid = np.invert(np.isnan(estimate_blurred_transformed.data))
        if image.mask_valid_pixels is not None:
            residuum_valid = np.logical_and(residuum_valid, image.mask_valid_pixels)
        residuum[residuum_valid] = (image.data[residuum_valid]
                                       - estimate_blurred_transformed.data[residuum_valid])

        image_residuum = Image(image_data=residuum.data)

        return image_residuum
