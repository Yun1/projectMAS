# This file is part of pyTSEB for processes related to the Monin-Obukhov Similarity Theory
# Copyright 2016 Hector Nieto and contributors listed in the README.md file.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Created on Apr 6 2015
@author: Hector Nieto (hnieto@ias.csic.es)

Modified on Jan 27 2016
@author: Hector Nieto (hnieto@ias.csic.es)

DESCRIPTION
===========
This package contains the main routines for estimating variables related to the Monin-Obukhov (MO) Similarity Theory,
such as  MO length, adiabatic correctors for heat and momentum transport and wind profile through a canopy. It
requires the following package.

* :doc:`meteoUtils` for the estimation of meteorological variables.

PACKAGE CONTENTS
================
* :func:`calc_L` Monin-Obukhov length.
* :func:`calc_richardson` Richardson number.
* :func:`calc_u_star` Friction velocity.

Stability correction functions
------------------------------
* :func:`calc_Psi_H` Adiabatic correction factor for heat transport.
* :func:`calc_Psi_M` Adiabatic correction factor for momentum transport.
* :func:`CalcPhi_M_Brutsaert` [Brutsaert1992]_ similarity function for momentum transfer.
* :func:`CalcPhi_H_Dyer` [Dyer1974]_ similarity function for heat transfer.
* :func:`CalcPhi_M_Dyer` [Dyer1974]_ similarity function for momentum transfer.

Wind profile functions
----------------------
* :func:`calc_u_C` [Norman1995]_ canopy wind speed.
* :func:`calc_u_C_star` MOST canopy wind speed.
* :func:`calc_u_Goudriaan` [Goudriaan1977]_ wind speed profile below the canopy.
* :func:`calc_A_Goudriaan` [Goudriaan1977]_ wind attenuation coefficient below the canopy.

"""

import numpy as np

from .meteo_utils import calc_lambda

#==============================================================================
# List of constants used in MO similarity
#==============================================================================
# von Karman's constant
k = 0.4
# acceleration of gravity (m s-2)
gravity = 9.8
# Drag coefficient (Goudriaan 1977)
c_d = 0.2
# Relative turbulence intensity (Goudriaan 1977)
i_w = 0.5


def calc_L(ustar, T_A_K, rho, c_p, H, LE):
    '''Calculates the Monin-Obukhov length.

    Parameters
    ----------
    ustar : float
        friction velocity (m s-1).
    T_A_K : float
        air temperature (Kelvin).
    rho : float
        air density (kg m-3).
    c_p : float
        Heat capacity of air at constant pressure (J kg-1 K-1).
    H : float
        sensible heat flux (W m-2).
    LE : float
        latent heat flux (W m-2).

    Returns
    -------
    L : float
        Obukhov stability length (m).

    References
    ----------
    .. [Brutsaert2005] Brutsaert, W. (2005). Hydrology: an introduction (Vol. 61, No. 8).
        Cambridge: Cambridge University Press.'''

    # Convert input scalars to numpy arrays
    ustar, T_A_K, rho, c_p, H, LE = map(
        np.asarray, (ustar, T_A_K, rho, c_p, H, LE))
    # first convert latent heat into rate of surface evaporation (kg m-2 s-1)
    Lambda = calc_lambda(T_A_K) * 1e6  # in J kg-1
    E = LE / Lambda

    # Virtual sensible heat flux
    Hv = H + (0.61 * T_A_K * c_p * E)

    L = np.asarray(np.ones(ustar.shape) * float('inf'))
    i = Hv != 0
    L_const = np.asarray(k * gravity / T_A_K)
    L[i] = -ustar[i]**3 / (L_const[i] * (Hv[i] / (rho[i] * c_p[i])))
    return np.asarray(L)


def calc_Psi_H(zoL):
    ''' Calculates the adiabatic correction factor for heat transport.

    Parameters
    ----------
    zoL : float
        stability coefficient (unitless).

    Returns
    -------
    Psi_H : float
        adiabatic corrector factor fof heat transport (unitless).

    References
    ----------
    .. [Brutsaert2005] Brutsaert, W. (2005). Hydrology: an introduction (Vol. 61, No. 8).
        Cambridge: Cambridge University Press.
    '''

    # Convert input scalars to numpy array
    zoL = np.asarray(zoL)
    Psi_H = np.zeros(zoL.shape)
    # for stable and netural (zoL = 0 -> Psi_H = 0) conditions
    a = 6.1
    b = 2.5
    Psi_H[zoL >= 0.0] = -a * \
        np.log(zoL[zoL >= 0.0] + (1.0 + zoL[zoL >= 0.0]**b)**(1. / b))
    # for unstable conditions
    y = -zoL
    c = 0.33
    d = 0.057
    n = 0.78
    Psi_H[zoL < 0.0] = ((1.0 - d) / n) * np.log((c + y[zoL < 0.0]**n) / c)
    return np.asarray(Psi_H)


def calc_Psi_M(zoL):
    ''' Adiabatic correction factor for momentum transport.

    Parameters
    ----------
    zoL : float
        stability coefficient (unitless).

    Returns
    -------
    Psi_M : float
        adiabatic corrector factor fof momentum transport (unitless).

    References
    ----------
    .. [Brutsaert2005] Brutsaert, W. (2005). Hydrology: an introduction (Vol. 61, No. 8).
        Cambridge: Cambridge University Press.
    '''

    # Convert input scalars to numpy array
    zoL = np.asarray(zoL)

    Psi_M = np.zeros(zoL.shape)
    # for stable and netural (zoL = 0 -> Psi_M = 0) conditions
    a = 6.1
    b = 2.5
    Psi_M[zoL >= 0.0] = -a * \
        np.log(zoL[zoL >= 0.0] + (1.0 + zoL[zoL >= 0.0]**b)**(1.0 / b))
    # for unstable conditions
    y = np.maximum(-zoL, 0.0)
    a = 0.33
    b = 0.41
    x = np.asarray((y / a)**0.333333)
    Psi_0 = -np.log(a) + 3**0.5 * b * a**0.333333 * np.pi / 6.0
    y = np.minimum(y, b**-3)
    i = zoL < 0
    Psi_M[i] = (np.log(a + y[i]) - 3.0 * b * y[i]**0.333333 +
                (b * a**0.333333) / 2.0 * np.log((1.0 + x[i])**2 / (1.0 - x[i] + x[i]**2)) +
                3.0**0.5 * b * a**0.333333 * np.arctan((2.0 * x[i] - 1.0) / 3**0.5) +
                Psi_0)
    return np.asarray(Psi_M)


def calc_richardson(u, z_u, d_0, T_R0, T_R1, T_A0, T_A1):
    '''Richardson number.

    Estimates the Bulk Richardson number for turbulence using
    time difference temperatures.

    Parameters
    ----------
    u : float
        Wind speed (m s-1).
    z_u : float
        Wind speed measurement height (m).
    d_0 : float
        Zero-plane displacement height (m).
    T_R0 : float
        radiometric surface temperature at time 0 (K).
    T_R1 : float
        radiometric surface temperature at time 1 (K).
    T_A0 : float
        air temperature at time 0 (K).
    T_A1 : float
        air temperature at time 1 (K).

    Returns
    -------
    Ri : float
        Richardson number.

    References
    ----------
    .. [Norman2000] Norman, J. M., W. P. Kustas, J. H. Prueger, and G. R. Diak (2000),
        Surface flux estimation using radiometric temperature: A dual-temperature-difference
        method to minimize measurement errors, Water Resour. Res., 36(8), 2263-2274,
        http://dx.doi.org/10.1029/2000WR900033.
    '''

    # See eq (2) from Louis 1979
    Ri = -(gravity * (z_u - d_0) / T_A1) * \
          (((T_R1 - T_R0) - (T_A1 - T_A0)) / u**2) # equation (12) [Norman2000]
    return np.asarray(Ri)


def calc_u_C(u_friction, h_C, d_0, z_0M):
    '''[Norman1995]_ wind speed at the canopy, reformulated to use u_friction

    Parameters
    ----------
    u_friction : float
        Wind friction velocity (m s-1).
    h_C : float
        canopy height (m).
    d_0 : float
        zero-plane displacement height.
    z_0M : float
        aerodynamic roughness length for momentum transport (m).

    Returns
    -------
    u_C : float
        wind speed at the canop interface (m s-1).

    References
    ----------
    .. [Norman1995] J.M. Norman, W.P. Kustas, K.S. Humes, Source approach for estimating
        soil and vegetation energy fluxes in observations of directional radiometric
        surface temperature, Agricultural and Forest Meteorology, Volume 77, Issues 3-4,
        Pages 263-293,
        http://dx.doi.org/10.1016/0168-1923(95)02265-Y.
    '''

    # The original equation below has been refolmulated to use u_friction:
    # u_C = u * log((h_C - d_0) / z_0M)/(log ((z_u  - d_0) / z_0M)- Psi_M)
    u_C = np.log((h_C - d_0) / z_0M) * u_friction / k
    return np.asarray(u_C)


def calc_u_C_star(u_friction, h_C, d_0, z_0M, L=float('inf')):
    ''' MOST wind speed at the canopy

    Parameters
    ----------
    u_friction : float
        friction velocity (m s-1).
    h_C : float
        canopy height (m).
    d_0 : float
        zero-plane displacement height.
    z_0M : float
        aerodynamic roughness length for momentum transport (m).
    L : float, optional
        Monin-Obukhov length (m).

    Returns
    -------
    u_C : float
        wind speed at the canop interface (m s-1).
    '''

    Psi_M = calc_Psi_M((h_C - d_0) / L)
    Psi_M0 = calc_Psi_M(z_0M / L)

    # calcualte u_C, wind speed at the top of (or above) the canopy
    u_C = (u_friction * (np.log((h_C - d_0) / z_0M) - Psi_M + Psi_M0)) / k
    return np.asarray(u_C)


def calc_u_Goudriaan(u_C, h_C, LAI, leaf_width, z):
    '''Estimates the wind speed at a given height below the canopy.

    Parameters
    ----------
    U_C : float
        Windspeed at the canopy interface (m s-1).
    h_C : float
        canopy height (m).
    LAI : float
        Efective Leaf (Plant) Area Index.
    leaf_width : float
        effective leaf width size (m).
    z : float
        heigh at which the windsped will be estimated.

    Returns
    -------
    u_z : float
        wind speed at height z (m s-1).

    References
    ----------
    .. [Norman1995] J.M. Norman, W.P. Kustas, K.S. Humes, Source approach for estimating
        soil and vegetation energy fluxes in observations of directional radiometric
        surface temperature, Agricultural and Forest Meteorology, Volume 77, Issues 3-4,
        Pages 263-293,
        http://dx.doi.org/10.1016/0168-1923(95)02265-Y.
    .. [Goudriaan1977] Goudriaan (1977) Crop micrometeorology: a simulation study
 '''

    # extinction factor for wind speed
    a = calc_A_Goudriaan(h_C, LAI, leaf_width)
    u_z = u_C * np.exp(-a * (1.0 - (z / h_C)))  # Eq. 4.48 in Goudriaan 1977
    return np.asarray(u_z)


def calc_A_Goudriaan(h_C, LAI, leaf_width):
    ''' Estimates the extinction coefficient factor for wind speed

    Parameters
    ----------
    h_C : float
        canopy height (m)
    LAI : float
        Efective Leaf (Plant) Area Index
    leaf_width : float
        effective leaf width size (m)

    Returns
    -------
    a : float
        exctinction coefficient for wind speed through the canopy

    References
    ----------
    .. [Goudriaan1977] Goudriaan (1977) Crop micrometeorology: a simulation study
    '''

    # Equation in Norman et al. 1995
    k3_prime = 0.28
    a = k3_prime * LAI**(2. / 3.) * h_C**(1. / 3.) * leaf_width**(-1. / 3.)

    return np.asarray(a)


def calc_u_star(u, z_u, L, d_0, z_0M, useRi=False):
    '''Friction velocity.

    Parameters
    ----------
    u : float
        wind speed above the surface (m s-1).
    z_u : float
        wind speed measurement height (m).
    L : float
        Obukhov stability length (m) or Richardson number, see useRi variable.
    d_0 : float
        zero-plane displacement height (m).
    z_0M : float
        aerodynamic roughness length for momentum transport (m).
    useRi : bool, optional
        Use the Richardson number istead of MO length for adiabatic correction factors.

    References
    ----------
    .. [Brutsaert2005] Brutsaert, W. (2005). Hydrology: an introduction (Vol. 61, No. 8).
        Cambridge: Cambridge University Press.
    '''

    # Covert input scalars to numpy arrays
    u, z_u, L, d_0, z_0M = map(np.asarray, (u, z_u, L, d_0, z_0M))
    if useRi:
        # use the approximation Ri ~ (z-d_0)./L from end of section 2.    2
        # from Norman et. al., 2000 (DTD paper)
        Psi_M = calc_Psi_M(L)
        Psi_M0 = calc_Psi_M(L / (z_u - d_0) * z_0M)
    else:
        # calculate correction factors in other conditions
        L[L == 0.0] = 1e-36
        Psi_M = calc_Psi_M((z_u - d_0) / L)
        Psi_M0 = calc_Psi_M(z_0M / L)
    u_star = u * k / (np.log((z_u - d_0) / z_0M) - Psi_M + Psi_M0)
    return np.asarray(u_star)
