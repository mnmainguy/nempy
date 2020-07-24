import numpy as np
import pandas as pd
from mip import Model, xsum, minimize, CONTINUOUS, OptimizationStatus, BINARY


class InterfaceToSolver:
    """A wrapper for the mip model class, allows interaction with mip using pd.DataFrames."""
    def __init__(self):
        self.variables = {}
        self.mip_model = Model("market")
        self.mip_model.verbose = 0
        self.dummy_binary_1 = None
        self.dummy_binary_2 = None

    def copy(self):
        """Add decision variables to the model.

        Examples
        --------
        >>> decision_variables = pd.DataFrame({
        ...   'variable_id': [0, 1],
        ...   'lower_bound': [0.0, 0.0],
        ...   'upper_bound': [6.0, 1.0],
        ...   'type': ['continuous', 'binary']})

        >>> si = InterfaceToSolver()

        >>> si.add_variables(decision_variables)

        >>> si_copy = si.copy()

        >>> print(si_copy.mip_model.num_cols)
        2

        The first one should have the following properties.

        >>> print(si_copy.mip_model.var_by_name('0').var_type)
        C

        >>> print(si_copy.mip_model.var_by_name('0').lb)
        0.0

        >>> print(si_copy.mip_model.var_by_name('0').ub)
        6.0

        The second one should have the following properties.

        >>> print(si_copy.mip_model.var_by_name('1').var_type)
        B

        >>> print(si_copy.mip_model.var_by_name('1').lb)
        0.0

        >>> print(si_copy.mip_model.var_by_name('1').ub)
        1.0
        """
        model_copy = InterfaceToSolver()
        model_copy.mip_model = self.mip_model.copy()
        for var in model_copy.mip_model.vars:
            model_copy.variables[int(var.name)] = var
        return model_copy

    def add_variables(self, decision_variables):
        """Add decision variables to the model.

        Examples
        --------
        >>> decision_variables = pd.DataFrame({
        ...   'variable_id': [0, 1],
        ...   'lower_bound': [0.0, 0.0],
        ...   'upper_bound': [6.0, 1.0],
        ...   'type': ['continuous', 'binary']})

        >>> si = InterfaceToSolver()

        >>> si.add_variables(decision_variables)

        The underlying mip_model should now have 2 variables.

        >>> print(si.mip_model.num_cols)
        2

        The first one should have the following properties.

        >>> print(si.mip_model.var_by_name('0').var_type)
        C

        >>> print(si.mip_model.var_by_name('0').lb)
        0.0

        >>> print(si.mip_model.var_by_name('0').ub)
        6.0

        The second one should have the following properties.

        >>> print(si.mip_model.var_by_name('1').var_type)
        B

        >>> print(si.mip_model.var_by_name('1').lb)
        0.0

        >>> print(si.mip_model.var_by_name('1').ub)
        1.0

        Parameters
        ----------
        decision_variables : pd.DataFrame

            =============  ===============================================================
            Columns:       Description:
            variable_id    the id of the variable (as `int`)
            lower_bound    the lower bound of the variable, is zero for bids (as `np.float64`)
            upper_bound    the upper bound of the variable, the volume bid (as `np.float64`)
            type           the type of variable, 'continuous' or 'binary'  (as `str`)
            =============  ===============================================================

        Returns
        -------

        """
        # Create a mapping between the nempy level names for variable types and the mip representation.
        variable_types = {'continuous': CONTINUOUS, 'binary': BINARY}
        # Add each variable to the mip model.
        for variable_id, lower_bound, upper_bound, variable_type in zip(
                list(decision_variables['variable_id']), list(decision_variables['lower_bound']),
                list(decision_variables['upper_bound']), list(decision_variables['type'])):

            self.variables[variable_id] = self.mip_model.add_var(lb=lower_bound, ub=upper_bound,
                                                                 var_type=variable_types[variable_type],
                                                                 name=str(variable_id))

    def remove_variables(self, variables_to_remove):
        """Add decision variables to the model.

        Examples
        --------
        >>> decision_variables = pd.DataFrame({
        ...   'variable_id': [0, 1],
        ...   'lower_bound': [0.0, 0.0],
        ...   'upper_bound': [6.0, 1.0],
        ...   'type': ['continuous', 'binary']})

        >>> variables_to_remove = pd.DataFrame({
        ...   'variable_id': [1]})

        >>> si = InterfaceToSolver()

        >>> si.add_variables(decision_variables)

        >>> print(si.mip_model.num_cols)
        2

        >>> si.remove_variables(variables_to_remove)

        >>> print(si.mip_model.num_cols)
        1

        >>> print(si.mip_model.var_by_name('0').var_type)
        C

        >>> print(si.mip_model.var_by_name('0').lb)
        0.0

        >>> print(si.mip_model.var_by_name('0').ub)
        6.0

        Parameters
        ----------
        decision_variables : pd.DataFrame

            =============  ===============================================================
            Columns:       Description:
            variable_id    the id of the variable (as `int`)
            lower_bound    the lower bound of the variable, is zero for bids (as `np.float64`)
            upper_bound    the upper bound of the variable, the volume bid (as `np.float64`)
            type           the type of variable, 'continuous' or 'binary'  (as `str`)
            =============  ===============================================================

        Returns
        -------

        """
        variables_to_remove['variable_id'].apply(lambda x: self.mip_model.remove(self.variables[x]))

    def add_sos_type_2(self, sos_variables, sos_id_columns, position_column):
        """Add groups of special ordered sets of type 2 two the mip model.

        Examples
        --------

        >>> decision_variables = pd.DataFrame({
        ...   'variable_id': [0, 1, 2, 3, 4, 5],
        ...   'lower_bound': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ...   'upper_bound': [5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
        ...   'type': ['continuous', 'continuous', 'continuous',
        ...            'continuous', 'continuous', 'continuous']})

        >>> sos_variables = pd.DataFrame({
        ...   'variable_id': [0, 1, 2, 3, 4, 5],
        ...   'sos_id': ['A', 'A', 'A', 'B', 'B', 'B'],
        ...   'position': [0, 1, 2, 0, 1, 2]})

        >>> si = InterfaceToSolver()

        >>> si.add_variables(decision_variables)

        >>> si.add_sos_type_2(sos_variables)

        Parameters
        ----------
        sos_variables : pd.DataFrame

            =============  ===============================================================
            Columns:       Description:
            variable_id    the unique identifier of the variable (as `np.int64`)
            sos_id         the unique identifier of each special ordered set (as `str`)
            position       the position of the variable in the special ordered set
                           (as `np.int64`)
            =============  ===============================================================

        Returns
        -------

        """

        # Function that adds sets to mip model.
        def add_sos_vars(sos_group):
            self.mip_model.add_sos(list(zip(sos_group['vars'], sos_group[position_column])), 2)
        # For each variable_id get the variable object from the mip model
        sos_variables['vars'] = sos_variables['variable_id'].apply(lambda x: self.variables[x])
        # Break up the sets based on their id and add them to the model separately.
        sos_variables.groupby(sos_id_columns).apply(add_sos_vars)
        # This is a hack to make mip knows there are binary constraints.
        self.mip_model.add_var(var_type=BINARY, obj=0.0)

    def add_sos_type_1(self, sos_variables):
        # Function that adds sets to mip model.
        def add_sos_vars(sos_group):
            self.mip_model.add_sos(list(zip(sos_group['vars'], [1.0 for i in range(len(sos_variables['vars']))])), 1)
        # For each variable_id get the variable object from the mip model
        sos_variables['vars'] = sos_variables['variable_id'].apply(lambda x: self.variables[x])
        # Break up the sets based on their id and add them to the model separately.
        sos_variables.groupby('sos_id').apply(add_sos_vars)
        # This is a hack to make mip knows there are binary constraints.
        self.mip_model.add_var(var_type=BINARY, obj=0.0)

    def add_objective_function(self, objective_function):
        """Add the objective function to the mip model.

        Examples
        --------

        >>> decision_variables = pd.DataFrame({
        ...   'variable_id': [0, 1, 2, 3, 4, 5],
        ...   'lower_bound': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ...   'upper_bound': [5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
        ...   'type': ['continuous', 'continuous', 'continuous',
        ...            'continuous', 'continuous', 'continuous']})

        >>> objective_function = pd.DataFrame({
        ...   'variable_id': [0, 1, 3, 4, 5],
        ...   'cost': [1.0, 2.0, -1.0, 5.0, 0.0]})

        >>> si = InterfaceToSolver()

        >>> si.add_variables(decision_variables)

        >>> si.add_objective_function(objective_function)

        >>> print(si.mip_model.var_by_name('0').obj)
        1.0

        >>> print(si.mip_model.var_by_name('5').obj)
        0.0

        Parameters
        ----------
        objective_function : pd.DataFrame

            =============  ===============================================================
            Columns:       Description:
            variable_id    the unique identifier of the variable (as `np.int64`)
            cost           the cost of the variable in model (as `np.float64`)
            =============  ===============================================================

        """
        objective_function = objective_function.sort_values('variable_id')
        objective_function = objective_function.set_index('variable_id')
        self.mip_model.objective = minimize(xsum(objective_function['cost'][i] * self.variables[i] for i in
                                                 list(objective_function.index)))

    def add_constraints(self, constraints_lhs, constraints_type_and_rhs):
        """Add constraints to the mip model.

        Examples
        --------
        >>> decision_variables = pd.DataFrame({
        ...   'variable_id': [0, 1, 2, 3, 4, 5],
        ...   'lower_bound': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ...   'upper_bound': [5.0, 5.0, 10.0, 10.0, 5.0, 5.0],
        ...   'type': ['continuous', 'continuous', 'continuous',
        ...            'continuous', 'continuous', 'continuous']})

        >>> constraints_lhs = pd.DataFrame({
        ...   'constraint_id': [1, 1, 2, 2],
        ...   'variable_id': [0, 1, 3, 4],
        ...   'coefficient': [1.0, 0.5, 1.0, 2.0]})

        >>> constraints_type_and_rhs = pd.DataFrame({
        ...   'constraint_id': [1, 2],
        ...   'type': ['<=', '='],
        ...   'rhs': [10.0, 20.0]})

        >>> si = InterfaceToSolver()

        >>> si.add_variables(decision_variables)

        >>> si.add_constraints(constraints_lhs, constraints_type_and_rhs)

        >>> print(si.mip_model.constr_by_name('1'))
        1: +1.0 0 +0.5 1 <= 10.0

        >>> print(si.mip_model.constr_by_name('2'))
        2: +1.0 3 +2.0 4 = 20.0


        Parameters
        ----------
        constraints_lhs : pd.DataFrame

            =============  ===============================================================
            Columns:       Description:
            variable_id    the unique identifier of the variable (as `np.int64`)
            constraint_id  the unique identifier of the constraint (as `np.int64`)
            coefficient    the coefficient of the variable in constraint (as `np.float64`)
            =============  ===============================================================

        constraints_type_and_rhs : pd.DataFrame

            =============  ===============================================================
            Columns:       Description:
            constraint_id  the unique identifier of the constraint (as `np.int64`)
            type           the direction of the constraint, can be '>=' '<=' or '='
                           (as 'str')
            rhs            the value on the right hand side of the constraint
                           (can be `np.int64` or a mip variable object)
            =============  ===============================================================

        Returns
        -------

        """

        # Transform the pd.DataFrame so each coefficient for a particular constraint is on an individual row.
        constraint_matrix = pd.pivot_table(constraints_lhs, 'coefficient', 'constraint_id', 'variable_id',
                                           aggfunc='sum')
        # Make sure columns and rows are ordered by name.
        constraint_matrix = constraint_matrix.sort_index(axis=1)
        constraint_matrix = constraint_matrix.sort_index()
        # Get the column and row ids as they won't be accessible after converting the constraint matrix to np.array
        column_ids = np.asarray(constraint_matrix.columns)
        row_ids = np.asarray(constraint_matrix.index)
        # Convert the constrain matrix to an np.array, makes adding the constraints to model much faster.
        constraint_matrix_np = np.asarray(constraint_matrix)

        # Make a dictionary so constraint rhs values can be accessed using the constraint id.
        rhs = dict(zip(constraints_type_and_rhs['constraint_id'], constraints_type_and_rhs['rhs']))
        # Make a dictionary so constraint type can be accessed using the constraint id.
        enq_type = dict(zip(constraints_type_and_rhs['constraint_id'], constraints_type_and_rhs['type']))
        for row, id in zip(constraint_matrix_np, row_ids):
            # Get the position of all non nan (i.e non zero) values in the constraint row.
            columns_in_constraint = np.argwhere(~np.isnan(row)).flatten()
            # Use the positions to get the is of non nan values in the constraint row.
            column_ids_in_constraint = column_ids[columns_in_constraint]
            # Use the variable_ids to get mip variable objects present in the constraint.
            lhs_variables = np.asarray([self.variables[k] for k in column_ids_in_constraint])
            # Use the positions of the non nan values to the lhs coefficients.
            lhs = row[columns_in_constraint]
            # Multiply and the variables by their coefficients and sum to create the lhs of the constraint.
            exp = lhs_variables * lhs
            exp = exp.tolist()
            exp = xsum(exp)
            # Add based on inequality type.
            if enq_type[id] == '<=':
                new_constraint = exp <= rhs[id]
            elif enq_type[id] == '>=':
                new_constraint = exp >= rhs[id]
            elif enq_type[id] == '=':
                new_constraint = exp == rhs[id]
            else:
                raise ValueError("Constraint type not recognised should be one of '<=', '>=' or '='.")
            self.mip_model.add_constr(new_constraint, name=str(id))

    def remove_constraints(self, constraints_to_remove):
        """Remove constraints from the mip model.

        Examples
        --------
        >>> decision_variables = pd.DataFrame({
        ...   'variable_id': [0, 1, 2, 3, 4, 5],
        ...   'lower_bound': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ...   'upper_bound': [5.0, 5.0, 10.0, 10.0, 5.0, 5.0],
        ...   'type': ['continuous', 'continuous', 'continuous',
        ...            'continuous', 'continuous', 'continuous']})

        >>> constraints_lhs = pd.DataFrame({
        ...   'constraint_id': [1, 1, 2, 2],
        ...   'variable_id': [0, 1, 3, 4],
        ...   'coefficient': [1.0, 0.5, 1.0, 2.0]})

        >>> constraints_type_and_rhs = pd.DataFrame({
        ...   'constraint_id': [1, 2],
        ...   'type': ['<=', '='],
        ...   'rhs': [10.0, 20.0]})

        >>> constraints_to_remove = pd.DataFrame({
        ...   'constraint_id': [1]})

        >>> si = InterfaceToSolver()

        >>> si.add_variables(decision_variables)

        >>> si.add_constraints(constraints_lhs, constraints_type_and_rhs)

        >>> print(si.mip_model.num_rows)
        2

        >>> print(si.mip_model.constr_by_name('1'))
        1: +1.0 0 +0.5 1 <= 10.0

        >>> print(si.mip_model.constr_by_name('2'))
        2: +1.0 3 +2.0 4 = 20.0

        >>> si.remove_constraints(constraints_to_remove)

        >>> print(si.mip_model.num_rows)
        1

        >>> print(si.mip_model.constr_by_name('2'))
        2: +1.0 3 +2.0 4 = 20.0

        """
        constraint_objects = constraints_to_remove['constraint_id'].apply(lambda x: self.mip_model.constr_by_name(str(x)))
        constraint_objects.apply(lambda x: self.mip_model.remove(x))

    def optimize(self):
        """Optimize the mip model.

        If an optimal solution cannot be found and the investigate_infeasibility flag is set to True then remove
        constraints until a feasible solution is found.

        Examples
        --------
        >>> decision_variables = pd.DataFrame({
        ...   'variable_id': [0, 1, 2, 3, 4, 5],
        ...   'lower_bound': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ...   'upper_bound': [5.0, 5.0, 10.0, 10.0, 5.0, 5.0],
        ...   'type': ['continuous', 'continuous', 'continuous',
        ...            'continuous', 'continuous', 'continuous']})

        >>> constraints_lhs = pd.DataFrame({
        ...   'constraint_id': [1, 1, 2, 2],
        ...   'variable_id': [0, 1, 3, 4],
        ...   'coefficient': [1.0, 0.5, 1.0, 2.0]})

        >>> constraints_type_and_rhs = pd.DataFrame({
        ...   'constraint_id': [1, 2],
        ...   'type': ['<=', '='],
        ...   'rhs': [10.0, 20.0]})

        >>> si = InterfaceToSolver()

        >>> si.add_variables(decision_variables)

        >>> si.add_constraints(constraints_lhs, constraints_type_and_rhs)

        >>> si.optimize()

        >>> decision_variables['value'] = si.get_optimal_values_of_decision_variables(decision_variables)

        >>> print(decision_variables)
           variable_id  lower_bound  upper_bound        type  value
        0            0          0.0          5.0  continuous    0.0
        1            1          0.0          5.0  continuous    0.0
        2            2          0.0         10.0  continuous    0.0
        3            3          0.0         10.0  continuous   10.0
        4            4          0.0          5.0  continuous    5.0
        5            5          0.0          5.0  continuous    0.0
        """
        status = self.mip_model.optimize()
        if status != OptimizationStatus.OPTIMAL:
            # Attempt find constraint causing infeasibility.
            print('Model infeasible attempting to find problem constraint.')
            con_index = find_problem_constraint(self.mip_model)
            print('Couldn\'t find an optimal solution, but removing con {} fixed INFEASIBLITY'.format(con_index))
            raise ValueError('Linear program infeasible')

    def get_optimal_values_of_decision_variables(self, variable_definitions):
        """Get the optimal values for each decision variable.

        Examples
        --------

        >>> decision_variables = pd.DataFrame({
        ...   'variable_id': [0, 1, 2, 3, 4, 5],
        ...   'lower_bound': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ...   'upper_bound': [5.0, 5.0, 10.0, 10.0, 5.0, 5.0],
        ...   'type': ['continuous', 'continuous', 'continuous',
        ...            'continuous', 'continuous', 'continuous']})

        >>> constraints_lhs = pd.DataFrame({
        ...   'constraint_id': [1, 1, 2, 2],
        ...   'variable_id': [0, 1, 3, 4],
        ...   'coefficient': [1.0, 0.5, 1.0, 2.0]})

        >>> constraints_type_and_rhs = pd.DataFrame({
        ...   'constraint_id': [1, 2],
        ...   'type': ['<=', '='],
        ...   'rhs': [10.0, 20.0]})

        >>> si = InterfaceToSolver()

        >>> si.add_variables(decision_variables)

        >>> si.add_constraints(constraints_lhs, constraints_type_and_rhs)

        >>> si.optimize()

        >>> decision_variables['value'] = si.get_optimal_values_of_decision_variables(decision_variables)

        >>> print(decision_variables)
           variable_id  lower_bound  upper_bound        type  value
        0            0          0.0          5.0  continuous    0.0
        1            1          0.0          5.0  continuous    0.0
        2            2          0.0         10.0  continuous    0.0
        3            3          0.0         10.0  continuous   10.0
        4            4          0.0          5.0  continuous    5.0
        5            5          0.0          5.0  continuous    0.0

        Parameters
        ----------
        variable_definitions : pd.DataFrame

            =============  ===============================================================
            Columns:       Description:
            variable_id    the unique identifier of the variable (as `np.int64`)
            =============  ===============================================================

        Returns
        -------
        values : pd.Series

        """
        values = variable_definitions['variable_id'].apply(lambda x: self.mip_model.var_by_name(str(x)).x,
                                                           self.mip_model)
        return values

    def get_slack_in_constraints(self, constraints_type_and_rhs):
        """Get the slack values in each constraint.

        Examples
        --------

        >>> decision_variables = pd.DataFrame({
        ...   'variable_id': [0, 1, 2, 3, 4, 5],
        ...   'lower_bound': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ...   'upper_bound': [5.0, 5.0, 10.0, 10.0, 5.0, 5.0],
        ...   'type': ['continuous', 'continuous', 'continuous',
        ...            'continuous', 'continuous', 'continuous']})

        >>> constraints_lhs = pd.DataFrame({
        ...   'constraint_id': [1, 1, 2, 2],
        ...   'variable_id': [0, 1, 3, 4],
        ...   'coefficient': [1.0, 0.5, 1.0, 2.0]})

        >>> constraints_type_and_rhs = pd.DataFrame({
        ...   'constraint_id': [1, 2],
        ...   'type': ['<=', '='],
        ...   'rhs': [10.0, 20.0]})

        >>> si = InterfaceToSolver()

        >>> si.add_variables(decision_variables)

        >>> si.add_constraints(constraints_lhs, constraints_type_and_rhs)

        >>> si.optimize()

        >>> constraints_type_and_rhs['slack'] = si.get_slack_in_constraints(constraints_type_and_rhs)

        >>> print(constraints_type_and_rhs)
           constraint_id type   rhs  slack
        0              1   <=  10.0   10.0
        1              2    =  20.0    0.0

        Parameters
        ----------
        variable_definitions : pd.DataFrame

            =============  ===============================================================
            Columns:       Description:
            constraint_id  the unique identifier of the constraint (as `np.int64`)
            =============  ===============================================================

        Returns
        -------
        slack : pd.Series

        """
        slack = constraints_type_and_rhs['constraint_id'].apply(lambda x: self.mip_model.constr_by_name(str(x)).slack,
                                                                self.mip_model)
        return slack

    def price_constraints(self, constraint_ids_to_price):
        """For each constraint_id find the marginal value of the constraint.

        This is done by incrementing the constraint by a value of 1.0 and re-optimizing the model, the marginal cost
        of the constraint is increase in the objective function value between model runs.

        Examples
        --------

        >>> decision_variables = pd.DataFrame({
        ...   'variable_id': [0, 1, 2, 3, 4, 5],
        ...   'lower_bound': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ...   'upper_bound': [5.0, 5.0, 10.0, 10.0, 5.0, 5.0],
        ...   'type': ['continuous', 'continuous', 'continuous',
        ...            'continuous', 'continuous', 'continuous']})

        >>> objective_function = pd.DataFrame({
        ...   'variable_id': [0, 1, 2, 3, 4, 5],
        ...   'cost': [1.0, 3.0, 10.0, 8.0, 9.0, 7.0]})

        >>> constraints_lhs = pd.DataFrame({
        ...   'constraint_id': [1, 1, 1, 1],
        ...   'variable_id': [0, 1, 3, 4],
        ...   'coefficient': [1.0, 1.0, 1.0, 1.0]})

        >>> constraints_type_and_rhs = pd.DataFrame({
        ...   'constraint_id': [1],
        ...   'type': ['='],
        ...   'rhs': [20.0]})

        >>> si = InterfaceToSolver()

        >>> si.add_variables(decision_variables)

        >>> si.add_constraints(constraints_lhs, constraints_type_and_rhs)

        >>> si.add_objective_function(objective_function)

        >>> si.optimize()

        >>> prices = si.price_constraints([1])

        >>> print(prices)
        {1: 8.0}

        >>> decision_variables['value'] = si.get_optimal_values_of_decision_variables(decision_variables)

        >>> print(decision_variables)
           variable_id  lower_bound  upper_bound        type  value
        0            0          0.0          5.0  continuous    5.0
        1            1          0.0          5.0  continuous    5.0
        2            2          0.0         10.0  continuous    0.0
        3            3          0.0         10.0  continuous   10.0
        4            4          0.0          5.0  continuous    0.0
        5            5          0.0          5.0  continuous    0.0

        Parameters
        ----------
        constraint_ids_to_price : list[int]

        Returns
        -------

        """
        costs = {}
        for id in constraint_ids_to_price:
            costs[id] = self.mip_model.constr_by_name(str(id)).pi
        return costs

    def update_rhs(self, constraint_id, violation_degree):
        constraint = self.mip_model.constr_by_name(str(constraint_id))
        constraint.rhs += violation_degree

    def disable_variables(self, variables):
        for var_id in variables['variable_id']:
            var = self.mip_model.var_by_name(str(var_id))
            var.lb = 0.0
            var.ub = 0.0


def find_problem_constraint(base_prob):
    cons = []
    test_prob = base_prob.copy()
    for con in [con.name for con in base_prob.constrs]:
        [test_prob.remove(c) for c in test_prob.constrs if c.name == con]
        status = test_prob.optimize()
        cons.append(con)
        if status == OptimizationStatus.OPTIMAL:
            return cons
    return []


def create_lhs(constraints, decision_variables, join_columns):
    """Combine constraints with general definitions of lhs with variables to give an explicit lhs definition.

    Both constraints and decision_variables can have a coefficient, the coefficient use in the actual lhs will
    be the product of the two coefficients.

    Examples
    --------

    >>> decision_variables = pd.DataFrame({
    ...   'variable_id': [0, 1, 2, 3, 4, 5],
    ...   'region': ['NSW', 'NSW', 'VIC',
    ...              'VIC', 'VIC', 'VIC'],
    ...   'service': ['energy', 'energy','energy',
    ...               'energy','energy','energy',],
    ...   'coefficient': [0.9, 0.8, 1.0, 0.95, 1.1, 1.01]})

    >>> constraints = pd.DataFrame({
    ...   'constraint_id': [1, 2],
    ...   'region': ['NSW', 'VIC'],
    ...   'service': ['energy', 'energy'],
    ...   'coefficient': [1.0, 1.0]})

    >>> lhs = create_lhs(decision_variables, constraints, ['region', 'service'])

    >>> print(lhs)
       constraint_id  variable_id  coefficient
    0              1            0         0.90
    1              1            1         0.80
    2              2            2         1.00
    3              2            3         0.95
    4              2            4         1.10
    5              2            5         1.01

    Parameters
    ----------
    constraints : pd.DataFrame

        =============  ===============================================================
        Columns:       Description:
        constraint_id  the unique identifier of the constraint (as `np.int64`)
        join_columns   one or more columns defining the types of variables that should
                       be on the lhs (as `str`)
        coefficient    the constraint level contribution to the lhs coefficient (as `np.float64`)
        =============  ===============================================================

    decision_variables : pd.DataFrame

        =============  ===============================================================
        Columns:       Description:
        variable_id    the unique identifier of the variable (as `np.int64`)
        join_columns   one or more columns defining the types of variables that should
                       be on the lhs (as `str`)
        coefficient    the variable level contribution to the lhs coefficient (as `np.float64`)
        =============  ===============================================================

    Returns
    -------
    lhs : pd.DataFrame

        =============  ===============================================================
        Columns:       Description:
        constraint_id  the unique identifier of the constraint (as `np.int64`)
        variable_id    the unique identifier of the variable (as `np.int64`)
        coefficient    the constraint level contribution to the lhs coefficient (as `np.float64`)
        =============  ===============================================================
    """
    constraints = pd.merge(constraints, decision_variables, 'inner', on=join_columns)
    constraints['coefficient'] = constraints['coefficient_x'] * constraints['coefficient_y']
    lhs = constraints.loc[:, ['constraint_id', 'variable_id', 'coefficient']]
    return lhs


def create_mapping_of_generic_constraint_sets_to_constraint_ids(constraints, market_constraints):
    """Combine generic constraints and fcas market constraints to get the full set of generic constraints.

    Returns non if there are no generic of fcas market constraints.

    Examples
    --------

    >>> constraints = {
    ...   'generic': pd.DataFrame({
    ...       'constraint_id': [0, 1],
    ...       'set': ['A', 'B']})
    ...   }

    >>> market_constraints = {
    ...   'fcas': pd.DataFrame({
    ...       'constraint_id': [2, 3],
    ...       'set': ['C', 'D']})
    ...   }

    >>> generic_constraints = create_mapping_of_generic_constraint_sets_to_constraint_ids(
    ... constraints, market_constraints)

    >>> print(generic_constraints)
       constraint_id set
    0              0   A
    1              1   B
    0              2   C
    1              3   D


    Parameters
    ----------
    constraints : dict{str : pd.DataFrame}

        The pd.DataFrame stored under the key 'generic', if it exists, should have the structure.

        =============  ===============================================================
        Columns:       Description:
        constraint_id  the unique identifier of the constraint (as `np.int64`)
        set            the constraint set that the id refers to (as `str`)
        =============  ===============================================================

    market_constraints : dict{str : pd.DataFrame}

        The pd.DataFrame stored under the key 'fcas', if it exists, should have the structure.

        =============  ===============================================================
        Columns:       Description:
        constraint_id  the unique identifier of the constraint (as `np.int64`)
        set            the constraint set that the id refers to (as `str`)
        =============  ===============================================================

    Returns
    -------
    pd.DataFrame or None

        If pd.DataFrame

        =============  ===============================================================
        Columns:       Description:
        constraint_id  the unique identifier of the constraint (as `np.int64`)
        set            the constraint set that the id refers to (as `str`)
        =============  ===============================================================

    """
    generic_constraints = []
    if 'generic' in constraints:
        generic_constraints.append(constraints['generic'].loc[:, ['constraint_id', 'set']])
    if 'fcas' in market_constraints:
        generic_constraints.append(market_constraints['fcas'].loc[:, ['constraint_id', 'set']])
    if len(generic_constraints) > 0:
        return pd.concat(generic_constraints)
    else:
        return None


def create_unit_level_generic_constraint_lhs(generic_constraint_units, generic_constraint_ids,
                                             unit_bids_to_constraint_map):
    """Find the lhs variables from units for generic constraints.

    Examples
    --------

    >>> generic_constraint_units = pd.DataFrame({
    ...   'set': ['A', 'A'],
    ...   'unit': ['X', 'Y'],
    ...   'service': ['energy', 'energy'],
    ...   'coefficient': [0.9, 0.8]})

    >>> generic_constraint_ids = pd.DataFrame({
    ...   'constraint_id': [1, 2],
    ...   'set': ['A', 'B']})

    >>> unit_bids_to_constraint_map = pd.DataFrame({
    ...   'variable_id': [0, 1],
    ...   'unit': ['X', 'Y'],
    ...   'service': ['energy', 'energy']})

    >>> lhs = create_unit_level_generic_constraint_lhs(generic_constraint_units, generic_constraint_ids,
    ...   unit_bids_to_constraint_map)

    >>> print(lhs)
       constraint_id  variable_id  coefficient
    0              1            0          0.9
    1              1            1          0.8

    Parameters
    ----------
    generic_constraint_units : pd.DataFrame

        =============  ==============================================================
        Columns:       Description:
        set            the unique identifier of the constraint set to map the
                       lhs coefficients to (as `str`)
        unit           the unit whose variables will be mapped to the lhs (as `str`)
        service        the service whose variables will be mapped to the lhs (as `str`)
        coefficient    the lhs coefficient (as `np.float64`)
        =============  ==============================================================

    generic_constraint_ids : pd.DataFrame

        =============  ===============================================================
        Columns:       Description:
        constraint_id  the unique identifier of the constraint (as `np.int64`)
        set            the constraint set that the id refers to (as `str`)
        =============  ===============================================================

    unit_bids_to_constraint_map : pd.DataFrame

        =============  =============================================================================
        Columns:       Description:
        variable_id    the id of the variable (as `np.int64`)
        unit           the unit level constraints the variable should map to (as `str`)
        service        the service type of the constraints the variables should map to (as `str`)
        =============  =============================================================================

    Returns
    -------
    lhs : pd.DataFrame

        =============  ===============================================================
        Columns:       Description:
        constraint_id  the unique identifier of the constraint (as `np.int64`)
        variable_id    the unique identifier of the variable (as `np.int64`)
        coefficient    the constraint level contribution to the lhs coefficient (as `np.float64`)
        =============  ===============================================================
    """
    unit_lhs = pd.merge(generic_constraint_units,
                        unit_bids_to_constraint_map.loc[:, ['unit', 'service', 'variable_id']],
                        on=['unit', 'service'])
    unit_lhs = pd.merge(unit_lhs, generic_constraint_ids.loc[:, ['constraint_id', 'set']], on='set')
    return unit_lhs.loc[:, ['constraint_id', 'variable_id', 'coefficient']]


def create_region_level_generic_constraint_lhs(generic_constraint_regions, generic_constraint_ids,
                                               regional_bids_to_constraint_map):
    """Find the lhs variables from regions for generic constraints.

    Examples
    --------

    >>> generic_constraint_regions = pd.DataFrame({
    ...   'set': ['A'],
    ...   'region': ['X'],
    ...   'service': ['energy'],
    ...   'coefficient': [0.9]})

    >>> generic_constraint_ids = pd.DataFrame({
    ...   'constraint_id': [1, 2],
    ...   'set': ['A', 'B']})

    >>> regional_bids_to_constraint_map = pd.DataFrame({
    ...   'variable_id': [0, 1],
    ...   'region': ['X', 'X'],
    ...   'service': ['energy', 'energy']})

    >>> lhs = create_region_level_generic_constraint_lhs(generic_constraint_regions, generic_constraint_ids,
    ...   regional_bids_to_constraint_map)

    >>> print(lhs)
       constraint_id  variable_id  coefficient
    0              1            0          0.9
    1              1            1          0.9

    Parameters
    ----------
    generic_constraint_regions : pd.DataFrame

        =============  ==============================================================
        Columns:       Description:
        set            the unique identifier of the constraint set to map the
                       lhs coefficients to (as `str`)
        region         the region whose variables will be mapped to the lhs (as `str`)
        service        the service whose variables will be mapped to the lhs (as `str`)
        coefficient    the lhs coefficient (as `np.float64`)
        =============  ==============================================================

    generic_constraint_ids : pd.DataFrame

        =============  ===============================================================
        Columns:       Description:
        constraint_id  the unique identifier of the constraint (as `np.int64`)
        set            the constraint set that the id refers to (as `str`)
        =============  ===============================================================

    regional_bids_to_constraint_map : pd.DataFrame

        =============  =============================================================================
        Columns:       Description:
        variable_id    the id of the variable (as `np.int64`)
        region         the region level constraints the variable should map to (as `str`)
        service        the service type of the constraints the variables should map to (as `str`)
        =============  =============================================================================

    Returns
    -------
    lhs : pd.DataFrame

        =============  ===============================================================
        Columns:       Description:
        constraint_id  the unique identifier of the constraint (as `np.int64`)
        variable_id    the unique identifier of the variable (as `np.int64`)
        coefficient    the constraint level contribution to the lhs coefficient (as `np.float64`)
        =============  ===============================================================
    """
    region_lhs = pd.merge(generic_constraint_regions,
                          regional_bids_to_constraint_map.loc[:, ['region', 'service', 'variable_id']],
                          on=['region', 'service'])
    region_lhs = pd.merge(region_lhs, generic_constraint_ids.loc[:, ['constraint_id', 'set']], on='set')
    return region_lhs.loc[:, ['constraint_id', 'variable_id', 'coefficient']]


def create_interconnector_generic_constraint_lhs(generic_constraint_interconnectors, generic_constraint_ids,
                                                 interconnector_variables):
    """Find the lhs variables from interconnectors for generic constraints.

    Examples
    --------

    >>> generic_constraint_interconnectors = pd.DataFrame({
    ...   'set': ['A'],
    ...   'interconnector': ['X'],
    ...   'coefficient': [0.9]})

    >>> generic_constraint_ids = pd.DataFrame({
    ...   'constraint_id': [1, 2],
    ...   'set': ['A', 'B']})

    >>> interconnector_variables = pd.DataFrame({
    ...   'variable_id': [0, 1],
    ...   'interconnector': ['X', 'X'],
    ...   'generic_constraint_factor': [1, 1]})

    >>> lhs = create_interconnector_generic_constraint_lhs(generic_constraint_interconnectors, generic_constraint_ids,
    ...   interconnector_variables)

    >>> print(lhs)
       constraint_id  variable_id  coefficient
    0              1            0          0.9
    1              1            1          0.9
    """
    interconnector_lhs = pd.merge(generic_constraint_interconnectors,
                                  interconnector_variables.loc[:, ['interconnector', 'variable_id', 'generic_constraint_factor']],
                                  on=['interconnector'])
    interconnector_lhs = pd.merge(interconnector_lhs, generic_constraint_ids.loc[:, ['constraint_id', 'set']], on='set')
    interconnector_lhs['coefficient'] = interconnector_lhs['coefficient'] * interconnector_lhs['generic_constraint_factor']
    return interconnector_lhs.loc[:, ['constraint_id', 'variable_id', 'coefficient']]

