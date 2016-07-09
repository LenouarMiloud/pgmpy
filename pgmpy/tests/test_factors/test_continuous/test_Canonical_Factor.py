import unittest

import numpy as np
import numpy.testing as np_test
from scipy.stats import multivariate_normal

from pgmpy.factors import JointGaussianDistribution as JGD
from pgmpy.factors import CanonicalFactor


class TestCanonicalFactor(unittest.TestCase):
    def test_class_init(self):
        phi = CanonicalFactor(['x1', ('y', 'z'), 'x3'],
                              np.array([[1.1, -1, 0], [-1, 4, -2], [0, -2, 4]]),
                              np.array([[1], [4.7], [-1]]), -2)
        self.assertEqual(phi.variables, ['x1', ('y', 'z'), 'x3'])
        np_test.assert_array_equal(phi.K, np.array([[1.1, -1, 0], [-1, 4, -2], [0, -2, 4]], dtype=float))
        np_test.assert_array_equal(phi.h, np.array([[1], [4.7], [-1]], dtype=float))
        self.assertEqual(phi.g, -2)
        self.assertEqual(phi.pdf, None)

        phi = CanonicalFactor(['x1', ('y', 'z'), 'x3'],
                              np.array([[1.1, -1, 0], [-1, 4, -2], [0, -2, 4]]),
                              np.array([1, 4.7, -1]), -2)
        self.assertEqual(phi.variables, ['x1', ('y', 'z'), 'x3'])
        np_test.assert_array_equal(phi.K, np.array([[1.1, -1, 0], [-1, 4, -2], [0, -2, 4]], dtype=float))
        np_test.assert_array_equal(phi.h, np.array([[1], [4.7], [-1]], dtype=float))
        self.assertEqual(phi.g, -2)
        self.assertEqual(phi.pdf, None)

        phi = CanonicalFactor(['x'], [[1]], [0], 1)
        self.assertEqual(phi.variables, ['x'])
        np_test.assert_array_equal(phi.K, np.array([[1]], dtype=float))
        np_test.assert_array_equal(phi.h, np.array([[0]], dtype=float))
        self.assertEqual(phi.g, 1)

    def test_class_init_valueerror(self):
        self.assertRaises(ValueError, CanonicalFactor, ['x1', 'x2', 'x3'],
                         np.array([[1.1, -1, 0], [-1, 4, -2], [0, -2, 4]]),
                         np.array([1, 2]), 7)
        self.assertRaises(ValueError, CanonicalFactor, ['x1', 'x2', 'x3'],
                         np.array([[1.1, -1, 0], [-1, 4], [0, -2, 4]]),
                         np.array([1, 2, 3]), 7)
        self.assertRaises(ValueError, CanonicalFactor, ['x1', 'x2', 'x3'],
                         np.array([[1.1, -1, 0], [0, -2, 4]]),
                         np.array([1, 2, 3]), 7)
        self.assertRaises(ValueError, CanonicalFactor, ['x1', 'x3'],
                         np.array([[1.1, -1, 0], [-1, 4, -2], [0, -2, 4]]),
                         np.array([1, 2, 3]), 7)


class TestJGDMethods(unittest.TestCase):
    def setUp(self):
        self.phi1 = CanonicalFactor(['x1', 'x2', 'x3'],
                                    np.array([[1.1, -1, 0], [-1, 4, -2], [0, -2, 4]]),
                                    np.array([[1], [4.7], [-1]]), -2)
        self.phi2 = CanonicalFactor(['x'], [[1]], [0], 1)
        self.phi3 = self.phi1.copy()

        self.gauss_phi1 = JGD(['x1', 'x2', 'x3'],
                              np.array([[3.13043478], [2.44347826], [0.97173913]]),
                              np.array([[ 1.30434783,  0.43478261,  0.2173913 ],
                                       [ 0.43478261,  0.47826087,  0.23913043],
                                       [ 0.2173913 ,  0.23913043,  0.36956522]], dtype=float))
        self.gauss_phi2 = JGD(['x'], np.array([0]), np.array([[1]]))

    def test_assignment(self):
        np_test.assert_almost_equal(self.phi1.assignment(*[1, 2, 3]), 1.217470031e-06)
        np_test.assert_almost_equal(self.phi2.assignment(1.234), 0.186314991823)

    def test_to_joint_gaussian(self):
        jgd1 = self.phi1.to_joint_gaussian()
        jgd2 = self.phi2.to_joint_gaussian()

        self.assertEqual(jgd1.variables, self.gauss_phi1.variables)
        np_test.assert_almost_equal(jgd1.covariance, self.gauss_phi1.covariance)
        np_test.assert_almost_equal(jgd1.mean, self.gauss_phi1.mean)

        self.assertEqual(jgd2.variables, self.gauss_phi2.variables)
        np_test.assert_almost_equal(jgd2.covariance, self.gauss_phi2.covariance)
        np_test.assert_almost_equal(jgd2.mean, self.gauss_phi2.mean)
