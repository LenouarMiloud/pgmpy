#!/usr/bin/env python3
import unittest
import numpy as np
from pgmpy.models import BayesianModel
from pgmpy.models import MarkovModel
from pgmpy.factors import Factor
from pgmpy.factors import TabularCPD
from pgmpy.inference import Inference


class TestInferenceBase(unittest.TestCase):
    def setUp(self):
        self.bayesian = BayesianModel([('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'e')])
        a_cpd = TabularCPD('a', 2, [[0.4, 0.6]])
        b_cpd = TabularCPD('b', 2, [[0.2, 0.4], [0.3, 0.4]], evidence='a', evidence_card=[2])
        c_cpd = TabularCPD('c', 2, [[0.1, 0.2], [0.3, 0.4]], evidence='b', evidence_card=[2])
        d_cpd = TabularCPD('d', 2, [[0.4, 0.3], [0.2, 0.1]], evidence='c', evidence_card=[2])
        e_cpd = TabularCPD('e', 2, [[0.3, 0.2], [0.4, 0.1]], evidence='d', evidence_card=[2])
        self.bayesian.add_cpds(a_cpd, b_cpd, c_cpd, d_cpd, e_cpd)

        self.markov = MarkovModel([('a', 'b'), ('b', 'd'), ('a', 'c'), ('c', 'd')])
        factor_1 = Factor(['a', 'b'], [2, 2], np.array([100, 1, 1, 100]))
        factor_2 = Factor(['a', 'c'], [2, 2], np.array([40, 30, 100, 20]))
        factor_3 = Factor(['b', 'd'], [2, 2], np.array([1, 100, 100, 1]))
        factor_4 = Factor(['c', 'd'], [2, 2], np.array([60, 60, 40, 40]))
        self.markov.add_factors(factor_1, factor_2, factor_3, factor_4)

    def test_bayesian_inference_init(self):
        infer_bayesian = Inference(self.bayesian)
        self.assertEqual(set(infer_bayesian.variables), {'a', 'b', 'c', 'd', 'e'})
        self.assertEqual(infer_bayesian.cardinality, {'a': 2, 'b': 2, 'c': 2, 'd': 2, 'e': 2})
        # self.assertEqual(infer_bayesian.factors, {'a': [self.bayesian.get_cpd('a').to_factor(),
        #                                                 self.bayesian.get_cpd('b').to_factor()],
        #                                           'b': [self.bayesian.get_cpd('b').to_factor(),
        #                                                 self.bayesian.get_cpd('c').to_factor()],
        #                                           'c': [self.bayesian.get_cpd('c').to_factor(),
        #                                                 self.bayesian.get_cpd('d').to_factor()],
        #                                           'd': [self.bayesian.get_cpd('d').to_factor(),
        #                                                 self.bayesian.get_cpd('e').to_factor()],
        #                                           'e': [self.bayesian.get_cpd('e').to_factor()]})

    def test_markov_inference_init(self):
        infer_markov = Inference(self.markov)
        self.assertEqual(set(infer_markov.variables), {'a', 'b', 'c', 'd'})
        self.assertEqual(infer_markov.cardinality, {'a': 2, 'b': 2, 'c': 2, 'd': 2})
        # self.assertEqual(infer_markov.factors, {'a': [Factor(['a', 'b'], [2, 2], np.array([100, 1, 1, 100])),
        #                                               Factor(['a', 'c'], [2, 2], np.array([40, 30, 100, 20]))],
        #                                         'b': [Factor(['a', 'b'], [2, 2], np.array([100, 1, 1, 100])),
        #                                               Factor(['b', 'd'], [2, 2], np.array([1, 100, 100, 1]))],
        #                                         'c': [Factor(['a', 'c'], [2, 2], np.array([40, 30, 100, 20])),
        #                                               Factor(['c', 'd'], [2, 2], np.array([60, 60, 40, 40]))],
        #                                         'd': [Factor(['b', 'd'], [2, 2], np.array([1, 100, 100, 1])),
        #                                               Factor(['c', 'd'], [2, 2], np.array([60, 60, 40, 40]))]})
