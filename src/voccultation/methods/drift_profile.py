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

from typing import List, Tuple
import numpy as np
import math

import voccultation.methods.drift_slice

from voccultation.data_structures.data_containers import DriftProfile, DriftSlice
from voccultation.methods.profile_deconvolution import wiener_deconvolution, generate_kernel

def smooth_track_profile(profile : DriftProfile, smooth : int) -> np.ndarray:
    """
    Smooths a track profile.

    Parameters:
        profile (DriftProfile): Profile to smooth
        smooth (int): Window size for smoothing

    Returns:
        np.ndarray: Smoothed profile
    """
    if smooth % 2 == 0:
        smooth += 1
    hw = int(smooth/2)
    L = profile.length
    average = np.zeros((L,))
    for x in range(L):
        s = []
        for y in range(x-hw,x+hw+1):
            if y < 0 or y >= L:
                continue
            s.append(profile.profile[y])
        average[x] = np.mean(s)
    return average

def calculate_reference_profile(reference_profiles : List[DriftProfile]) -> DriftProfile:
    """
    Calculates the mean reference profile.

    Parameters:
        reference_profiles (List[DriftProfile]): List of reference profiles

    Returns:
        DriftProfile: Mean reference profile
    """
    L = reference_profiles[0].profile.shape[0]
    mean_profile = np.zeros((L,))
    N = len(reference_profiles)
    for n in range(N):
        mean_profile += reference_profiles[n].profile
    mean_profile /= np.mean(mean_profile)
    errs = np.zeros((L,))
    for n in range(N):
        profile = reference_profiles[n].profile
        profile = profile / np.mean(profile)
        errs += (profile - mean_profile)**2/N
    errs = np.sqrt(errs)
    return DriftProfile(mean_profile, errs)

def calculate_sky_profile(sky_profiles : List[DriftProfile]) -> DriftProfile:
    """
    Calculates the sky profile parallel to track.
    Uses linear polynomial approximation for true sky brighness along track

    Parameters:
        sky_profiles (List[DriftProfile]): List of sky profiles

    Returns:
        DriftProfile: Sky profile
    """
    L = sky_profiles[0].length
    N = len(sky_profiles)
    xs = np.zeros((L*N,))
    ys = np.zeros((L*N,))
    for s in range(L):
        for n in range(N):
            xs[s*N+n] = s
            ys[s*N+n] = sky_profiles[n].profile[s]
    polynom = np.polynomial.Polynomial.fit(xs, ys, 1)
    values = polynom(xs)
    ds = ys - values
    stdev_val = np.sqrt(np.mean(ds**2))
    stdev = np.ones((L,))*stdev_val
    xs = np.array(range(L))
    values = polynom(xs)
    return DriftProfile(values, stdev)

def compensate_reference_profile(drift_profile : DriftProfile,
                                 reference_profile : DriftProfile) -> DriftProfile:
    """
    Compensates a profile using a reference profile.

    Parameters:
        drift_profile (DriftProfile): Profile to compensate
        reference_profile (DriftProfile): Reference profile

    Returns:
        DriftProfile: Compensated profile
    """
    return drift_profile
