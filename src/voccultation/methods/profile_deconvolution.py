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

import numpy as np

def generate_kernel(sigma: float, size: int) -> np.ndarray:
    """
    Generate 1D Gaussian kernel

    Parameters:
        sigma (float): Standard deviation of the normal distribution.
        size (int): Size of the generated kernel.
    Returns:
        np.ndarray: Generated Gaussian kernel.
    """
    x = np.linspace(-size//2, size//2 - 1, size)
    grid = np.outer(np.ones(size), x)
    kernel = np.exp(-((grid / sigma)**2) / 2.0)
    return kernel



def wiener_deconvolution(blurred_data: np.ndarray, kernel: np.ndarray, snr: float) -> np.ndarray:
    """
    Perform 1D Wiener deconvolution on blurred data.

    Parameters:
        blurred_data (np.ndarray): The blurred input data to be deconvolved.
        kernel (np.ndarray): The convolution kernel (point spread function).
        snr (float): Signal-to-noise ratio for Wiener filtering.

    Returns:
        np.ndarray: Deconvolved data.
    """
    # Ensure kernel is normalized
    kernel = kernel / np.sum(kernel)

    # Compute the Fourier transform of the kernel
    kernel_fft = np.fft.fft(kernel, n=len(blurred_data))

    # Compute the Wiener filter in frequency domain
    # Wiener filter: H* / (|H|^2 + 1/SNR)
    wiener_filter = np.conj(kernel_fft) / (np.abs(kernel_fft)**2 + 1/snr)

    # Apply the filter to the blurred data in frequency domain
    blurred_fft = np.fft.fft(blurred_data)
    deconvolved_fft = blurred_fft * wiener_filter

    # Transform back to time domain
    deconvolved_data = np.fft.ifft(deconvolved_fft).real

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
