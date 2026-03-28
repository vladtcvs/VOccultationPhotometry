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

from voccultation.data_structures.data_containers import DriftProfile
from voccultation.methods.profile_deconvolution import wiener_deconvolution

def smooth_track_profile(profile : DriftProfile, smooth : int) -> np.ndarray:
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
    """Calculate mean reference profile
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
    """Calculate sky profile parallel to track.
       We use linear polynomial approximation for true sky brighness along track
       I_sky(s) = a*s + b,
       where s is a index along track
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
    return drift_profile


def calculate_true_drift_profile(drift_profile : DriftProfile,
                                 side_profiles : List[DriftProfile],
                                 reference_profile : DriftProfile,
                                 params : dict) -> Tuple[DriftProfile, dict]:
    L = drift_profile.length
    for side_profile in side_profiles:
        assert side_profile.length==L

    # average sky profile parallel to occ profile
    sky_profile = calculate_sky_profile(side_profiles)

    # remove sky profile
    if params["remove_sky"]:
        drift_profile.profile = drift_profile.profile - sky_profile.profile

    # estimate errors
    smoothed = smooth_track_profile(drift_profile, 3)
    delta = np.sqrt(np.sum((smoothed - drift_profile.profile)**2)/L)
    mean = np.mean(drift_profile.profile)
    stats = {
        "mean" : mean,
        "stdev" : delta,
        "sky_stdev" : np.mean(sky_profile.error),
    }
    true_profile = DriftProfile(drift_profile.profile, np.sqrt(sky_profile.error**2))
    return true_profile, stats

def reference_profile_time_analyze(profile : np.ndarray) -> np.ndarray:
    """Find such time of each point of profile, that stretching profile according to such times, make it flat"""
    L = profile.shape[0]
    smooth_window = int(L / 8)
    smoothed = smooth_track_profile(profile, smooth_window)
    speed = 1 / smoothed
    speed = smooth_track_profile(speed, smooth_window)
    
    dts = 1 / speed
    T = np.sum(dts)
    return dts * L / T

def profile_according_to_time(profile : np.ndarray, dtimes : np.ndarray):
    return profile / dtimes
