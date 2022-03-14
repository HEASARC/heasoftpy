# -*- coding: utf-8 -*-

# CONTAINS TECHNICAL DATA/COMPUTER SOFTWARE DELIVERED TO THE U.S. GOVERNMENT WITH UNLIMITED RIGHTS
#
# Contract No.: CA 80MSFC17M0022
# Contractor Name: Universities Space Research Association
# Contractor Address: 7178 Columbia Gateway Drive, Columbia, MD 21046
#
# Copyright 2018-2022 by Universities Space Research Association (USRA). All rights reserved.
#
# Use by Non-US Government recipients is allowed by a BSD 3-Clause "Revised" Licensed detailed
# below:
#
# Developed by: William H. Cleveland Jr. and Erick A. Verleye
#               Universities Space Research Association
#               Science and Technology Institute
#               https://sti.usra.edu
#
# Redistribution and use in source and binary forms, with or without modification, are permitted
# provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of
#    conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of
#    conditions and the following disclaimer in the documentation and/or other materials provided
#    with the distribution.
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to
#    endorse or promote products derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import math
import numpy as np
from scipy.spatial.transform import Rotation as Rot


class Vector:
    """
    Encapsulates a Cartesian 3D vector.
    This vector does not have to be a unit vector, as the length is calculated
    so that it can be normalized as needed.
    """

    def __init__(self, x: float, y: float, z: float):
        """
        Sets the Cartesian x, y, and z values and calculates the length.

        Args:
            x (float): Cartesian x-axis component (dimensions irrelevant)
            y (float): Cartesian y-axis component (dimensions irrelevant)
            z (float): Cartesian z-axis component (dimensions irrelevant)

        Returns:
            None
        """
        if (np.size(x) != np.size(y)) or (np.size(x) != np.size(z)):
            raise ValueError('Axis arrays not the same size.')

        self._x = x
        self._y = y
        self._z = z

    @classmethod
    def from_radec(cls, ra: float, dec: float):
        """
        Converts RA and Dec to an ECI (Earth-Centered Inertial) unit vector.  Note
        that the resulting vector is a unit vector.  Uses this vector to
        construct an Vector object.

        Args:
            ra (float): Right ascension (radians)
            dec (float): Declination (radians)

        Returns:
            New Vector object constructed from RA, Dec.
        """
        x = np.cos(dec) * np.cos(ra)
        y = np.cos(dec) * np.sin(ra)
        z = np.sin(dec)

        return cls(x, y, z)

    def __mul__(self, other: float):
        return Vector(self.x * other, self.y * other, self.z * other)

    def __add__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

        return Vector(self.x + other, self.y + other, self.z + other)

    def __sub__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

        return Vector(self.x - other, self.y - other, self.y - other)

    def __eq__(self, other):
        if isinstance(other, Vector):
            return (np.array_equal(self.x, other.x) and
                    np.array_equal(self.y, other.y) and
                    np.array_equal(self.z, other.z))
        return False

    def to_radec(self):
        """
        Assumes Vector coordinates are ECI (Earth-Centered Inertial), and
        converts it to RA and Dec.  This vector need not be a unit vector.

        Args:

        Returns:
            ra (float): Right ascension (radians)
            dec (float): Declination (radians)
        """
        dec = np.arcsin(self.z / self.length)
        ra = np.arctan2(self.y, self.x)

        return ra, dec

    def to_components(self):
        """
        Outputs the x, y, z components of the vector.

        Args:

        Returns:
            x (float): x-axis component (dimensionless)
            y (float): y-axis component (dimensionless)
            z (float): z-axis component (dimensionless)
        """
        return self.x, self.y, self.z

    def to_array(self):
        """
        Outputs the vector as a numpy array of shape (N, 3), where N is the
            number of entries in each x, y, z array when the Vector was
            created.

        Args:

        Returns:
            carray (numpy.array): Array of x, y, z components, so it has shape N,3.
        """
        return np.array([self.x, self.y, self.z]).transpose()

    def dot(self, evec):
        """
        Calculates the dot product (a . b) between this vector (a) and another
        eci vector (b).  The result is a scalar.

        Args:
            evec (Vector): Vector to which angle is calculated.

        Returns:
            dotprod (float): Dot product between this and input vector.
        """
        dotprod = self.x * evec.x + self.y * evec.y + self.z * evec.z
        return dotprod

    def calc_angle(self, evec):
        """
        Uses the definition of the vector dot product:
            a . b = ||a|| ||b|| cos(Theta)
        to calculate the angle between two Vector objects.

        Args:
            evec (Vector): Vector to which angle is calculated.

        Returns
            theta (float): Angle between this vector and input vector.
        """
        dotprod = self.dot(evec)
        theta = np.arccos(dotprod / (self.length * evec.length))

        return theta

    def dot_angle(self, evec):
        """
        Calculates the dot product (a . b) between this Vector (a) and another
        Vector (b).  Also calculates the angle between them and returns
        both.

        Args:
            evec (Vector): Vector to which angle is calculated.

        Returns:
            dotprod (float): Dot product between this and input vector.
            theta (float): Angle between this vector and input vector.
        """
        dotprod = self.dot(evec)
        theta = np.arccos(dotprod / (self.length * evec.length))

        return dotprod, theta

    def cross(self, evec):
        """
        Calculates the cross product (a X b) between this vector (a) and
        another Vector (b).  The result (c) is also an Vector.

        Args:
            evec (Vector): Vector to which the cross product is calculated.

        Returns:
            crossprod (Vector): Resulting cross product vector.
        """
        crossprod = Vector((self.y * evec.z) - (self.z * evec.y),
                           -((self.x * evec.z) - (self.z * evec.x)),
                           (self.x * evec.y) - (self.y * evec.x))
        return crossprod

    def cross_angle(self, evec):
        """
        Calculates the cross product (a X b) between this vector (a) and
        the input Vector (b).  The result (c) is also an Vector.  Then
        it uses the magnitudes of the three vector to calculate the angle
        theta between the original vectors by the cross product formulat:
            ||a x b|| = ||a|| ||b|| sin(theta)

        Args:
            evec (Vector): Vector to which the cross product is calculated.

        Returns:
            crossprod (Vector): Resulting cross product vector.
            theta (float): Angle between this and the input vector.
        """
        crossprod = self.cross(evec)
        theta = np.arcsin(crossprod.length / (self.length * evec.length))

        return crossprod, theta

    def normalize(self):
        len = self.length
        return Vector(self.x / len, self.y / len, self.z / len)

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def z(self):
        return self._z

    @property
    def length(self):
        return np.sqrt(np.square(self.x) + np.square(self.y) + np.square(self.z))


class Quaternion:
    """
    Encapsulates the functionality of a quaternion.
    """

    def __init__(self, xval: float, yval: float, zval: float, scalar: float):
        """
        Creates the quaternion from its four components.

        Args:
            xval (float): X-axis component of quaternion.
            yval (float): Y-axis component of quaternion.
            zval (float): Z-axis component of quaternion.
            scalar (float): Scalar component of quaternion.
        """
        self._xval = xval
        self._yval = yval
        self._zval = zval
        self._scalar = scalar
        self._qarr = np.array([self._xval, self._yval, self._zval, self._scalar])
        self._rotation = Rot.from_quat(self._qarr)

    @staticmethod
    def _self_check(verification_vector, vec2: Vector):
        if isinstance(vec2, Vector):
            vec2 = vec2.to_array()

        for i in range(3):
            try:
                assert math.isclose(verification_vector[i], vec2[i], abs_tol=1e-7)
            except AssertionError:
                raise ValueError('Self check failed. Vectors may be anti-parallel or their magnitudes unequal')

    @classmethod
    def from_axis_angle(cls, axis: Vector, angle_deg: float):
        """
        Creates the quaternion from the axis-angle constructor.

        Args:
            axis (Vector): Vector representation of axis of rotation.
            angle_deg (float): Angle of rotation about axis in degrees.
        """
        hang = np.radians(angle_deg) * 0.5
        avec = axis.normalize() * np.sin(hang)
        return cls(avec.x, avec.y, avec.z, np.cos(hang))

    @classmethod
    def from_vector_pair(cls, vec1: Vector, vec2: Vector):
        """
        Creates a rotation operator from a pair of vector arrays.
            Args:
                vec1 (Vector): First vector in the pair by which the quaternion is defined.
                vec2 (Vector): Second vector in the pair by which the quaternion is defined.
        """
        # Normalize both vectors in the pair
        vec1 = vec1.normalize()
        vec2 = vec2.normalize()

        pair_cross = vec1.cross(vec2)
        pair_dot = vec1.dot(vec2)

        quaternion = [pair_cross.x, pair_cross.y, pair_cross.z, 1 + pair_dot] / np.linalg.norm(
            [pair_cross.x, pair_cross.y, pair_cross.z, 1 + pair_dot])

        xval = quaternion[0]
        yval = quaternion[1]
        zval = quaternion[2]
        scalar = quaternion[3]

        # Make sure the quaternion rotates the first vector into the second vector
        rotation = Rot.from_quat(quaternion)
        verification_vector = rotation.apply([vec1.x, vec1.y, vec1.z])
        cls._self_check(verification_vector, vec2)

        return cls(xval, yval, zval, scalar)

    @classmethod
    def from_array_pair(cls, array1: np.array, array2: np.array):
        """
        Creates a rotation operator from a pair of vector arrays.
            Args:
                array1 (np.array): First array in the pair by which the quaternion is defined.
                array2 (np.array): Second array in the pair by which the quaternion is defined.
        """
        # Normalize both vectors in the pair
        vec1 = array1 / np.linalg.norm(array1)
        vec2 = array2 / np.linalg.norm(array2)

        pair_cross = np.cross(vec1, vec2)

        quaternion = [*pair_cross, 1 + np.dot(vec1, vec2)] / np.linalg.norm([*pair_cross, 1 + np.dot(vec1, vec2)])

        xval = quaternion[0]
        yval = quaternion[1]
        zval = quaternion[2]
        scalar = quaternion[3]

        # Make sure the quaternion rotates the first vector into the second vector
        rotation = Rot.from_quat(quaternion)
        verification_vector = rotation.apply(vec1)
        cls._self_check(verification_vector, vec2)

        return cls(xval, yval, zval, scalar)

    @classmethod
    def from_matrix(cls, matrix: np.array):
        """
        Creates a quaternion object from a rotation matrix.
        Args:
            matrix (np.array): 3x3 rotation matrix representing desired quaternion
        """
        r = Rot.from_matrix(matrix).as_quat()

        return cls(r[0], r[1], r[2], r[3])

    def normalize(self):
        """
        Normalizes the quaternion.

        Args:

        Returns:
            nquat (Quaternion): Normalized version of this quaternion.
        """
        """
        length = np.sqrt(np.square(self._xval) + np.square(self._yval) +
                         np.square(self._zval) + np.square(self._scalar))
        """
        length = np.linalg.norm(self._qarr)
        return Quaternion(self._xval / length, self._yval / length,
                          self._zval / length, self._scalar / length)

    def to_array(self):
        """
        Converts the components to a numpy.array object.  To be compatible with
            scipy.spatial.transform.Rotation.from_quat, the quaternion array is
            scalar-last format.

        Args:

        Returns:
            qarray (numpy.array): Scalar-last array of quaternion components.
        """
        return np.array([self._xval, self._yval, self._zval, self._scalar])

    def to_matrix(self):
        """
        Converts the quaternion into a rotation matrix.

        Args:

        Returns:
            rot_matrix (numpy.array): Rotation matrix representing the quaternion.
        """

        return Rot.from_quat(self.to_array()).as_matrix()

    def inverse(self):
        """
        Calculates a quaternion that is the inverse of the current quaternion.

        Args:

        Returns:
            Quaternion that is the inverse of the current quaternion.
        """
        return Quaternion(-self._xval, -self._yval, -self._zval, self._scalar)

    def rotate(self, vector: Vector):
        """
        Uses the quaternion to rotate a vector (using scipy.spatial.transform.Rotation)

        Args:
            vector (Vector): Vector to be rotated.

        Returns
            rvec (Vector): Vector resulting from rotation.
        """
        # apply Quaternion rotation to vector.
        rvector = self._rotation.apply(vector.to_array())
        return Vector(rvector.transpose()[0], rvector.transpose()[1],
                      rvector.transpose()[2])

    def __mul__(self, other):
        return Quaternion(self._xval * other._scalar + self._yval * other._zval -
                          self._zval * other._yval + self._scalar * other._xval,
                          -self._xval * other._zval + self._yval * other._scalar +
                          self._zval * other._xval + self._scalar * other._yval,
                          self._xval * other._yval - self._yval * other._xval +
                          self._zval * other._scalar + self._scalar * other._zval,
                          -self._xval * other._xval - self._yval * other._yval -
                          self._zval * other._zval + self._scalar * other._scalar)
