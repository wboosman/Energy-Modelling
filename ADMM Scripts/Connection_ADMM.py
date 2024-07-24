class EConnection:
    """A class that represent the flow from a node to a line

    Attributes:
        line (Line): The corresponding Line to the terminal
        power (model variables): The variables that represent the decision of power on the terminal in the optimization model
        penalty term (list): List of values, for each time period one, that represent the penalty for the nodal optimization model
    """
    
    def __init__(self, name=None):
        """Initialize a new Line object. This is a change """

        self.name = "Electric Connection" if name is None else name
        self.network = None 
        self.device = None

    def _init_problem(self, model, time_horizon):
        """Initialize the variables beloinging to the line class that are importatn for the optimization model. """
        self._power = model.addVars(time_horizon,lb = -100, name=f"{self.name}_Variable")
        # Update the model to integrate the new variable
        self._prevPower = [0]*time_horizon
        self._penalty_term = [0]*time_horizon


    def updatePenalty(self):
        """Updates the penalty term for the terminal, used in the optimization model"""
        duals = self.network.dual
        average = self.network.balance
        self._penalty_term  =[x - y - z for x, y, z in zip(self._prevPower, average, duals)]

    @property
    def powerVariables(self):
        """Power variables representing sending (positive value) or receiving (negative value) at this
        terminal."""
        return self._power
    
    @property
    def powerValues(self):
        """Power send (positive value) or received (negative value) at this
        terminal."""
        return [var.x for var in self._power.values()]
    
    @property
    def penaltyTerm(self):
        return self._penalty_term
    
    @property
    def prevPower(self):
        return self._prevPower
    
    def getTotalPayment(self):
        """Method to get the weighted sum of values using the coefficients from C"""
        return sum(p * marginal_cost for p, marginal_cost in zip(self.powerValues, self.network.dual))

    def getHourlyPayment(self):
        """Method to get the weighted sum of values using the coefficients from C"""
        return [p * marginal_cost for p, marginal_cost in zip(self.powerValues, self.network.dual)]
    

    def set_network(self, network):
        """Setter function that automatically sets the corresponding network to the line once the line is initialized"""
        self.network = network

    def set_device(self, device):
        """Setter function that automatically sets the corresponding network to the line once the line is initialized"""
        self.device = device


    def set_prev_power(self):
        """Set the previous power equal to the current power valuesm, therefore saves the output of the optimizattion model, 
        and these values are in the next iteration used to calculate the pernalty term"""
        self._prevPower = self.powerValues


#########################################################################################################################################


class HConnection:
    """A class that represent the flow from a node to a line

    Attributes:
        line (Line): The corresponding Line to the terminal
        power (model variables): The variables that represent the decision of power on the terminal in the optimization model
        penalty term (list): List of values, for each time period one, that represent the penalty for the nodal optimization model
    """
    def __init__(self, name=None):
        """Initialize a new Line object. This is a change """

        self.name = "Thermal Connection" if name is None else name
        self.network = None 
        self.device = None

    def _init_problem(self, model, time_horizon):
        """Initialize the variables beloinging to the line class that are importatn for the optimization model. """
        self._heat = model.addVars(time_horizon,lb=-100,  name=f"{self.name}_Variable")
        self._prevHeat = [0]*time_horizon
        self._penalty_term = [0]*time_horizon

    def updatePenalty(self):
        """Updates the penalty term for the terminal, used in the optimization model"""
        duals = self.network.dual
        average = self.network.balance
        self._penalty_term  =[x - y - z for x, y, z in zip(self._prevHeat, average, duals)]

    @property
    def heatVariables(self):
        """Power variables representing sending (positive value) or receiving (negative value) at this
        terminal."""
        return self._heat
    
    @property
    def heatValues(self):
        """Power send (positive value) or received (negative value) at this
        terminal."""
        return [var.X for var in self._heat.values()]
    
    @property
    def penaltyTerm(self):
        return self._penalty_term
    
    @property
    def prevPower(self):
        return self._prevPower
    
    def getTotalPayment(self):
        """Method to get the weighted sum of values using the coefficients from C"""
        return sum(p * marginal_cost for p, marginal_cost in zip(self.heatValues, self.network.dual))

    def getHourlyPayment(self):
        """Method to get the weighted sum of values using the coefficients from C"""
        return [p * marginal_cost for p, marginal_cost in zip(self.heatValues, self.network.dual)]
    
    def set_network(self, network):
        """Setter function that automatically sets the corresponding network to the line once the line is initialized"""
        self.network = network

    def set_device(self, device):
        """Setter function that automatically sets the corresponding network to the line once the line is initialized"""
        self.device = device


    def set_prev_heat(self):
        """Set the previous power equal to the current power valuesm, therefore saves the output of the optimizattion model, 
        and these values are in the next iteration used to calculate the pernalty term"""
        self._prevHeat = self.heatValues
