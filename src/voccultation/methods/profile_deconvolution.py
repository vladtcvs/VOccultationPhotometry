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

def wiener_deconvolution(signal : np.ndarray, kernel : np.ndarray, snr : float):
    """
    Perform 1D Wiener deconvolution.

    Parameters
    ----------
    signal : np.ndarray
        Blurred/noisy observed signal (y = h * x + noise)
    kernel : np.ndarray
        Point spread function / impulse response (h)
    snr : float
        Signal-to-Noise Ratio (higher = less regularization, lower = more smoothing)

    Returns
    -------
    deconvolved : ndarray
        Estimated original signal
    """
    
    # Zero-pad kernel to same length as signal
    kernel_padded = np.zeros_like(signal)
    kernel_padded[:len(kernel)] = kernel

    # Fourier transforms
    H = np.fft.fft(kernel_padded)
    Y = np.fft.fft(signal)

    # Wiener filter in frequency domain
    # |H|^2 + 1/SNR
    H_conj = np.conj(H)
    denominator = (H * H_conj) + (1.0 / snr)

    # Apply filter
    X_est = (H_conj / denominator) * Y

    # Back to time domain
    deconvolved = np.real(np.fft.ifft(X_est))
    return deconvolved
