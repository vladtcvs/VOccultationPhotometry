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
from typing import List
from io import BytesIO

import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("Agg")

def plot_to_numpy(xrange : np.ndarray,
                  datas : List[np.ndarray],
                  width=800,
                  height=600,
                  dpi=100) -> np.ndarray:
    """
    Convert numerical data plot to numpy array

    Parameters:
    xrange : np.ndarray - x values
    datas: List[np.ndarray] - y values
    width: plot width in pixels
    height: plot height in pixels
    dpi: dots per inch

    Returns:
    numpy array of shape (height, width, 4) containing RGBA values
    """
    # Create figure
    fig = plt.figure(figsize=(width/dpi, height/dpi), dpi=dpi)

    # Plot the data
    args = []
    for data in datas:
        args.append(xrange)
        args.append(data)
    plt.plot(*args, linewidth=2)
    plt.grid(True)

    # Save plot to bytes buffer
    buf = BytesIO()
    plt.savefig(buf, format='rgba', dpi=dpi)
    buf.seek(0)

    # Convert buffer to numpy array
    img_array = np.frombuffer(buf.getvalue(), dtype=np.uint8)
    img_array = img_array.reshape(height, width, 4)
    img_array = img_array[:,:,0:3]

    # Clean up
    plt.close(fig)
    buf.close()

    return img_array
