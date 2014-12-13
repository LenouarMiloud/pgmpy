import functools
import numpy as np
from collections import OrderedDict
from pgmpy.exceptions import Exceptions

np.seterr(divide='raise')


class Factor:
    """
    Base class for *Factor*.

    Public Methods
    --------------
    assignment(index)
    get_cardinality(variable)
    marginalize([variable_list])
    normalize()
    product(*Factor)
    reduce([variable_values_list])
    """

    def __init__(self, variables, cardinality, value):
        """
        Initialize a factors class.

        Defined above, we have the following mapping from variable
        assignments to the index of the row vector in the value field:

        +-----+-----+-----+-------------------+
        |  x1 |  x2 |  x3 |    phi(x1, x2, x2)|
        +-----+-----+-----+-------------------+
        | x1_0| x2_0| x3_0|     phi.value(0)  |
        +-----+-----+-----+-------------------+
        | x1_0| x2_0| x3_1|     phi.value(1)  |
        +-----+-----+-----+-------------------+
        | x1_0| x2_1| x3_0|     phi.value(2)  |
        +-----+-----+-----+-------------------+
        | x1_0| x2_1| x3_1|     phi.value(3)  |
        +-----+-----+-----+-------------------+
        | x1_1| x2_0| x3_0|     phi.value(4)  |
        +-----+-----+-----+-------------------+
        | x1_1| x2_0| x3_1|     phi.value(5)  |
        +-----+-----+-----+-------------------+
        | x1_1| x2_1| x3_0|     phi.value(6)  |
        +-----+-----+-----+-------------------+
        | x1_1| x2_1| x3_1|     phi.value(7)  |
        +-----+-----+-----+-------------------+

        Parameters
        ----------
        variables: list
            List of scope of factor
        cardinality: list, array_like
            List of cardinality of each variable
        value: list, array_like
            List or array of values of factor.
            A Factor's values are stored in a row vector in the value
            using an ordering such that the left-most variables as defined in
            the variable field cycle through their values the fastest. More
            concretely, for factor

        Examples
        --------
        >>> from pgmpy.factors import Factor
        >>> phi = Factor(['x1', 'x2', 'x3'], [2, 2, 2], np.ones(8))
        """
        self.variables = OrderedDict()
        if len(variables) != len(cardinality):
            raise ValueError("The size of variables and cardinality should be same")
        for variable, card in zip(variables, cardinality):
            self.variables[variable] = [variable + '_' + str(index)
                                        for index in range(card)]
        self.cardinality = np.array(cardinality)
        self.values = np.array(value, dtype=np.double)
        if not self.values.shape[0] == np.prod(self.cardinality):
            raise Exceptions.SizeError("Incompetant value array")

    def scope(self):
        """
        Returns the scope of the factor.

        Examples
        --------
        >>> from pgmpy.factors import Factor
        >>> phi = Factor(['x1', 'x2', 'x3'], [2, 3, 2], np.ones(8))
        >>> phi.scope()
        ['x1', 'x2', 'x3']
        """
        return list(self.variables)

    def assignment(self, index):
        """
        Returns a list of assignments for the corresponding index.

        Parameters
        ----------
        index: integer, list-type, ndarray
            index or indices whose assignment is to be computed

        Examples
        --------
        >>> import numpy as np
        >>> from pgmpy.factors import Factor
        >>> phi = Factor(['diff', 'intel'], [2, 2], np.ones(4))
        >>> phi.assignment([1, 2])
        [['diff_0', 'intel_1'], ['diff_1', 'intel_0']]
        """
        if not isinstance(index, np.ndarray):
            index = np.atleast_1d(index)
        max_index = np.prod(self.cardinality) - 1
        if not all(i <= max_index for i in index):
            raise IndexError("Index greater than max possible index")
        assignments = []
        for ind in index:
            assign = []
            for card in self.cardinality[::-1]:
                assign.insert(0, ind % card)
                ind = ind/card
            assignments.append(map(int, assign))
        return [[self.variables[key][val] for key, val in
                 zip(self.variables.keys(), values)] for values in assignments]

    def get_cardinality(self, variable):
        """
        Returns cardinality of a given variable

        Parameters
        ----------
        variable: string

        Examples
        --------
        >>> from pgmpy.factors import Factor
        >>> phi = Factor(['x1', 'x2', 'x3'], [2, 3, 2], range(12))
        >>> phi.get_cardinality('x1')
        2
        """
        if variable not in self.variables:
            raise Exceptions.ScopeError("%s not in scope" % variable)
        return self.cardinality[list(self.variables.keys()).index(variable)]

    def identity_factor(self):
        """
        Returns the identity factor.

        When the identity factor of a factor is multiplied with the factor
        it returns the factor itself.

        Examples
        --------
        >>> from pgmpy.factors import Factor
        >>> phi = Factor(['x1', 'x2', 'x3'], [2, 3, 2], range(12))
        >>> phi_identity = phi.identity_factor()
        >>> phi_identity.variables
        OrderedDict([('x1', ['x1_0', 'x1_1']), ('x2', ['x2_0', 'x2_1', 'x2_2']), ('x3', ['x3_0', 'x3_1'])])
        >>> phi_identity.values
        array([ 1.,  1.,  1.,  1.,  1.,  1.,  1.,  1.,  1.,  1.,  1.,  1.])
        """
        return Factor(self.variables, self.cardinality, np.ones(np.product(self.cardinality)))

    def marginalize(self, variables, inplace=True):
        """
        Modifies the factor with marginalized values.

        Parameters
        ----------
        variables: string, list-type
            name of variable to be marginalized

        inplace: boolean
            If inplace=True it will modify the factor itself, else would return
            a new factor

        Examples
        --------
        >>> from pgmpy.factors import Factor
        >>> phi = Factor(['x1', 'x2', 'x3'], [2, 3, 2], range(12))
        >>> phi.marginalize(['x1', 'x3'])
        >>> phi.values
        array([ 14.,  22.,  30.])
        >>> phi.variables
        OrderedDict([('x2', ['x2_0', 'x2_1', 'x2_2'])])
        """
        if not isinstance(variables, list):
            variables = [variables]
        for variable in variables:
            if variable not in self.variables:
                raise Exceptions.ScopeError("%s not in scope" % variable)

        if inplace:
            factor = self
        else:
            factor = Factor(self.scope(), self.cardinality, self.values)

        for variable in variables:
            factor.values = factor._marginalize_single_variable(variable)
            index = list(factor.variables.keys()).index(variable)
            del(factor.variables[variable])
            factor.cardinality = np.delete(factor.cardinality, index)

        if not inplace:
            return factor

    def _marginalize_single_variable(self, variable):
        """
        Returns marginalised factor for a single variable

        Parameters
        ---------
        variable_name: string
            name of variable to be marginalized

        """
        index = list(self.variables.keys()).index(variable)
        cum_cardinality = (np.product(self.cardinality) /
                           np.concatenate(([1], np.cumprod(self.cardinality)))).astype(np.int64, copy=False)
        num_elements = cum_cardinality[0]
        sum_index = [j for i in range(0, num_elements,
                                      cum_cardinality[index])
                     for j in range(i, i+cum_cardinality[index+1])]
        marg_factor = np.zeros(num_elements/self.cardinality[index])
        for i in range(self.cardinality[index]):
            marg_factor += self.values[np.array(sum_index) +
                                       i*cum_cardinality[index+1]]
        return marg_factor

    def normalize(self, inplace=True):
        """
        Normalizes the values of factor so that they sum to 1.

        Parameters
        ----------
        inplace: boolean
            If inplace=True it will modify the factor itself, else would return
            a new factor

        Examples
        --------
        >>> from pgmpy.factors import Factor
        >>> phi = Factor(['x1', 'x2', 'x3'], [2, 3, 2], range(12))
        >>> norm_phi = phi.normalize()
        >>> norm_phi.values
        array([ 0.        ,  0.01515152,  0.03030303,  0.04545455,  0.06060606,
                0.07575758,  0.09090909,  0.10606061,  0.12121212,  0.13636364,
                0.15151515,  0.16666667])

        """
        if inplace:
            self.values = self.values / np.sum(self.values)
        else:
            factor = Factor(self.scope(), self.cardinality, self.values)
            factor.values = factor.values / np.sum(factor.values)
            return factor

    def reduce(self, values, inplace=True):
        """
        Reduces the factor to the context of given variable values.

        Parameters
        ----------
        values: string, list-type
            name of the variable values

        inplace: boolean
            If inplace=True it will modify the factor itself, else would return
            a new factor

        Examples
        --------
        >>> from pgmpy.factors import Factor
        >>> phi = Factor(['x1', 'x2', 'x3'], [2, 3, 2], range(12))
        >>> phi.reduce(['x1_0', 'x2_0'])
        >>> phi.values
        array([0., 1.])
        """
        if not isinstance(values, list):
            values = [values]

        if inplace:
            factor = self
        else:
            factor = Factor(self.scope(), self.cardinality, self.values)

        for value in values:
            if not '_' in value:
                raise TypeError("Values should be in the form of "
                                "variablename_index")
            var, value_index = value.split('_')
            if not var in factor.variables:
                raise Exceptions.ScopeError("%s not in scope" % var)
            index = list(factor.variables.keys()).index(var)
            if not (int(value_index) < factor.cardinality[index]):
                raise Exceptions.SizeError("Value is "
                                           "greater than max possible value")
            cum_cardinality = (np.product(factor.cardinality) /
                               np.concatenate(([1], np.cumprod(factor.cardinality)))).astype(np.int64, copy=False)
            num_elements = cum_cardinality[0]
            index_arr = [j for i in range(0, num_elements,
                                          cum_cardinality[index])
                         for j in range(i, i+cum_cardinality[index+1])]
            factor.values = factor.values[np.array(index_arr) + int(value_index) * cum_cardinality[index+1]]
            del(factor.variables[var])
            factor.cardinality = np.delete(factor.cardinality, index)

        if not inplace:
            return factor

    def product(self, *factors):
        """
        Returns the factor product with factors.

        Parameters
        ----------
        *factors: Factor1, Factor2, ...
            Factors to be multiplied

        Example
        -------
        >>> from pgmpy.factors import Factor
        >>> phi1 = Factor(['x1', 'x2', 'x3'], [2, 3, 2], range(12))
        >>> phi2 = Factor(['x3', 'x4', 'x1'], [2, 2, 2], range(8))
        >>> phi = phi1.product(phi2)
        >>> phi.variables
        OrderedDict([('x1', ['x1_0', 'x1_1']), ('x2', ['x2_0', 'x2_1', 'x2_2']),
                ('x3', ['x3_0', 'x3_1']), ('x4', ['x4_0', 'x4_1'])])
        """
        return factor_product(self, *factors)

    def divide(self, factor):
        """
        Returns a new factors instance after division by factor.

        Parameters
        ----------
        factor : factors
            The denominator

        Examples
        --------
        >>> from pgmpy.factors import Factor
        >>> phi1 = Factor(['x1', 'x2', 'x3'], [2, 3, 2], range(12))
        >>> phi2 = Factor(['x3', 'x1'], [2, 2], [x+1 for x in range(4)])
        >>> phi = phi1.divide(phi2)
        >>> phi
        x1	x2	x3	phi(x1, x2, x3)
        x1_0	x2_0	x3_0	0.0
        x1_1	x2_0	x3_0	0.5
        x1_0	x2_1	x3_0	0.666666666667
        x1_1	x2_1	x3_0	0.75
        x1_0	x2_2	x3_0	4.0
        x1_1	x2_2	x3_0	2.5
        x1_0	x2_0	x3_1	2.0
        x1_1	x2_0	x3_1	1.75
        x1_0	x2_1	x3_1	8.0
        x1_1	x2_1	x3_1	4.5
        x1_0	x2_2	x3_1	3.33333333333
        x1_1	x2_2	x3_1	2.75
        """
        return factor_divide(self, factor)

    def __str__(self):
        return self._str('phi')

    def _str(self, phi_or_p):
        string = ""
        for var in self.variables:
            string += str(var) + "\t\t"
        string += phi_or_p + '(' + ', '.join(self.variables) + ')'
        string += "\n"
        string += '-' * 2 * len(string) + '\n'

        #fun and gen are functions to generate the different values of variables in the table.
        #gen starts with giving fun initial value of b=[0, 0, 0] then fun tries to increment it
        #by 1.
        def fun(b, index=len(self.cardinality)-1):
            b[index] += 1
            if b[index] == self.cardinality[index]:
                b[index] = 0
                fun(b, index-1)
            return b

        def gen():
            b = [0] * len(self.variables)
            yield b
            for i in range(np.prod(self.cardinality)-1):
                yield fun(b)

        value_index = 0
        for prob in gen():
            prob_list = [list(self.variables)[i] + '_' + str(prob[i]) for i in range(len(self.variables))]
            string += '\t\t'.join(prob_list) + '\t\t' + str(self.values[value_index]) + '\n'
            value_index += 1

        return string

    def __mul__(self, other):
        return self.product(other)

    def __eq__(self, other):
        if type(self) != type(other):
            return False

        if self.variables == other.variables and all(self.cardinality == other.cardinality) \
                and all(self.values == other.values):
            return True
        else:
            return False

    def __hash__(self):
        """
        Returns the hash of the factor object based on the scope of the factor.
        """
        return hash(' '.join(self.variables) + ' '.join(map(str, self.cardinality)) +
                    ' '.join(list(map(str, self.values))))


def _bivar_factor_operation(phi1, phi2, operation):
    """
    Returns product of two factors.

    Parameters
    ----------
    phi1: factors

    phi2: factors

    operation: M | D
            M: multiplies phi1 and phi2
            D: divides phi1 by phi2
    See Also
    --------
    factor_product
    """
    phi1_vars = list(phi1.variables)
    phi2_vars = list(phi2.variables)
    common_var_list = [var for var in phi1_vars if var in phi2_vars]
    if common_var_list:
        variables = phi1_vars
        variables.extend([var for var in phi2.variables
                         if var not in common_var_list])
        cardinality = list(phi1.cardinality)
        cardinality.extend(phi2.get_cardinality(var) for var in phi2.variables
                           if var not in common_var_list)

        phi1_indexes = [i for i in range(len(phi1.variables))]
        phi2_indexes = [variables.index(var) for var in phi2.variables]
        values = []
        phi1_cumprod = np.delete(np.concatenate((np.array([1]), np.cumprod(phi1.cardinality[::-1])), axis=1)[::-1], 0)
        phi2_cumprod = np.delete(np.concatenate((np.array([1]), np.cumprod(phi2.cardinality[::-1])), axis=1)[::-1], 0)
        from itertools import product
        if operation == 'M':
            for index in product(*[range(card) for card in cardinality]):
                index = np.array(index)
                values.append(phi1.values[np.sum(index[phi1_indexes] * phi1_cumprod)] *
                              phi2.values[np.sum(index[phi2_indexes] * phi2_cumprod)])
        elif operation == 'D':
            for index in product(*[range(card) for card in cardinality]):
                index = np.array(index)
                try:
                    values.append(phi1.values[np.sum(index[phi1_indexes] * phi1_cumprod)] /
                                  phi2.values[np.sum(index[phi2_indexes] * phi2_cumprod)])
                except FloatingPointError:
                    # zero division error should return 0. ref Koller page 365, Fig 10.7
                    values.append(0)

        phi = Factor(variables, cardinality, values)
        return phi
    else:
        values = np.array([])
        if operation == 'M':
            for value in phi1.values:
                values = np.concatenate((values, value*phi2.values), axis=1)
        elif operation == 'D':
            # reference: Koller Defination 10.7
            raise ValueError("factors Division not defined for factors with no common scope")
        variables = phi1_vars + phi2_vars
        cardinality = list(phi1.cardinality) + list(phi2.cardinality)
        phi = Factor(variables, cardinality, values)
        return phi


def factor_product(*args):
    """
    Returns factor product of multiple factors.

    Parameters
    ----------
    factor1, factor2, .....: factors
        factors to be multiplied

    Examples
    --------
    >>> from pgmpy.factors import Factor, factor_product
    >>> phi1 = Factor(['x1', 'x2', 'x3'], [2, 3, 2], range(12))
    >>> phi2 = Factor(['x3', 'x4', 'x1'], [2, 2, 2], range(8))
    >>> phi = factor_product(phi1, phi2)
    >>> phi.variables
    OrderedDict([('x1', ['x1_0', 'x1_1']), ('x2', ['x2_0', 'x2_1', 'x2_2']),
                ('x3', ['x3_0', 'x3_1']), ('x4', ['x4_0', 'x4_1'])])

    See Also
    --------
    factor_divide
    """
    # if not all(isinstance(phi, Factor) for phi in args):
    #     raise TypeError("Input parameters must be factors")
    return functools.reduce(lambda phi1, phi2: _bivar_factor_operation(phi1, phi2, operation='M'), args)


def factor_divide(phi1, phi2):
    """
    Returns new factors instance equal to phi1/phi2.

    Parameters
    ----------
    phi1: factors
        The Dividend.

    phi2: factors
        The Divisor.

    Examples
    --------
    Examples
    --------
    >>> from pgmpy.factors import Factor, factor_divide
    >>> phi1 = Factor(['x1', 'x2', 'x3'], [2, 3, 2], range(12))
    >>> phi2 = Factor(['x3', 'x1'], [2, 2], [x+1 for x in range(4)])
    >>> assert isinstance(phi1, Factor)
    >>> assert isinstance(phi2, Factor)
    >>> phi = factor_divide(phi1, phi2)
    >>> phi
    x1	x2	x3	phi(x1, x2, x3)
    x1_0	x2_0	x3_0	0.0
    x1_1	x2_0	x3_0	0.5
    x1_0	x2_1	x3_0	0.666666666667
    x1_1	x2_1	x3_0	0.75
    x1_0	x2_2	x3_0	4.0
    x1_1	x2_2	x3_0	2.5
    x1_0	x2_0	x3_1	2.0
    x1_1	x2_0	x3_1	1.75
    x1_0	x2_1	x3_1	8.0
    x1_1	x2_1	x3_1	4.5
    x1_0	x2_2	x3_1	3.33333333333
    x1_1	x2_2	x3_1	2.75

    See Also
    --------
    factor_product
    """
    if not isinstance(phi1, Factor) or not isinstance(phi2, Factor):
        raise TypeError("phi1 and phi2 should be factors instances")
    return _bivar_factor_operation(phi1, phi2, operation='D')
