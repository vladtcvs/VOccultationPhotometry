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

def generate_kernel(sigma: float, half_width: int) -> np.ndarray:
    """
    Generate 2D Gaussian kernel

    Parameters:
        sigma (float): Standard deviation of the Gaussian kernel
        half_width (int): Half-width of the kernel ortogonal to drift

    Returns:
        np.ndarray: Generated Gaussian kernel.
    """
    sigma = max(sigma, 0.5)
    y = np.linspace(-half_width, half_width, 2*half_width + 1)
    x = np.linspace(-half_width, half_width, 2*half_width + 1)
    xv, yv = np.meshgrid(x, y, indexing='xy')
    kernel = np.exp(-( (xv ** 2 + yv**2) / sigma**2) / 2.0)
    kernel = kernel / np.sum(kernel)
    return kernel

def wiener_deconvolution(blurred_data: np.ndarray, kernel: np.ndarray, snr: float) -> np.ndarray:
    """
    Perform 2D Wiener deconvolution on blurred data.

    Parameters:
        blurred_data (np.ndarray): 2-D blurred input data to be deconvolved.
        kernel (np.ndarray): 2-D convolution kernel (point spread function).
        snr (float): Signal-to-noise ratio for Wiener filtering.

    Returns:
        np.ndarray: Deconvolved data.
    """
    slice_length = blurred_data.shape[0]
    slice_width = blurred_data.shape[1]
    kernel_length = kernel.shape[0]
    kernel_width = kernel.shape[1]
    print(f"Deconvolution. Slices {slice_length}x{slice_width}, kernel {kernel_length}x{kernel_width}")
    assert kernel_width <= slice_width
    assert kernel_length <= slice_width
    pad_length = (slice_length - kernel_length)//2
    pad_width = (slice_width - kernel_width)//2
    kernel_padded = np.zeros(blurred_data.shape)
    kernel_padded[pad_length:pad_length+kernel_length,pad_width:pad_width+kernel_width] = kernel

    kernel_fft = np.fft.fft2(kernel_padded)
    kernel_fft = np.fft.fftshift(kernel_fft)
    kernel_fft_conj = np.conj(kernel_fft)
    wiener = kernel_fft_conj / (kernel_fft * kernel_fft_conj + 1/snr)

    blurred_fft = np.fft.fft2(blurred_data)
    blurred_fft = np.fft.fftshift(blurred_fft)

    deconvolved_fft = blurred_fft * wiener
    deconvolved_fft = np.fft.ifftshift(deconvolved_fft)
    deconvolved_data = np.fft.ifft2(deconvolved_fft)

    return np.real(deconvolved_data)

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

