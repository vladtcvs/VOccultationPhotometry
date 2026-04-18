#
# Copyright (c) 2026 Vladislav Tsendrovskii
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#


from skimage import restoration
import numpy as np

def generate_kernel(sigma: float, length : int, half_width: int) -> np.ndarray:
    """
    Generate 2D Gaussian kernel

    Parameters:
        sigma (float): Standard deviation of the Gaussian kernel
        length (int): Length of the kernel along the drift
        half_width (int): Half-width of the kernel ortogonal to drift

    Returns:
        np.ndarray: Generated Gaussian kernel.
    """
    if length % 2 == 0:
        length = length + 1

    sigma = max(sigma, 0.5)
    x = np.linspace(-length//2, length//2, length)
    y = np.linspace(-half_width, half_width, 2*half_width + 1)
    xv, yv = np.meshgrid(x, y, indexing='xy')
    kernel = np.exp(-( (xv ** 2 + yv**2) / sigma**2) / 2.0)
    kernel = kernel / np.sum(kernel)
    return kernel

def wiener_deconvolution(blurred_data: np.ndarray, kernel: np.ndarray, snr: float) -> np.ndarray:
    """
    Perform 2D Wiener deconvolution on blurred data.

    Parameters:
        blurred_data (np.ndarray): The blurred input data to be deconvolved.
        kernel (np.ndarray): The convolution kernel (point spread function).
        snr (float): Signal-to-noise ratio for Wiener filtering.

    Returns:
        np.ndarray: Deconvolved data.
    """
    deconvolved, _ = restoration.wiener(blurred_data, kernel, 0.1)


    return deconvolved_data

def estimate_snr(star_track: np.ndarray, empty_tracks: np.ndarray) -> float:
    """
    Estimate SNR of a star track based on a single star track and multiple empty tracks with only sky glow.

    Star track = Poisson(true signal + sky glow signal)
    Empty tracks = only sky glow signal (Poisson)
    All Poisson distributions can be multiplied by unknown constant

    Parameters:
        star_track (np.ndarray): Single star track (1D array)
        empty_tracks (np.ndarray): Array of empty tracks with only sky glow (2D array, each row is a track)

    Returns:
        float: Estimated SNR value
    """
    # Calculate mean of empty tracks (sky glow only)
    empty_mean = np.mean(empty_tracks, axis=0)

    # Estimate the true signal by subtracting sky glow from the star track
    # Since we're dealing with Poisson distributions, we need to be careful
    # The difference should be the true signal (assuming no negative values)
    signal_estimate = np.maximum(star_track - empty_mean, 0)

    # Calculate variance of empty tracks (which represents sky glow variance)
    empty_var = np.var(empty_tracks, axis=0)

    # Estimate SNR for each point
    # SNR = signal / sqrt(variance of noise)
    # Since we're dealing with Poisson noise, variance = signal + background
    # But we're estimating background from empty tracks, so:
    # SNR = signal / sqrt(background)
    snr_values = np.zeros_like(signal_estimate)

    # Avoid division by zero
    mask = empty_var > 0
    snr_values[mask] = signal_estimate[mask] / np.sqrt(empty_var[mask])

    # Return the mean SNR across all points (excluding invalid values)
    valid_snr = snr_values[np.isfinite(snr_values)]

    if len(valid_snr) > 0:
        return np.mean(valid_snr)
    else:
        return 0.0

