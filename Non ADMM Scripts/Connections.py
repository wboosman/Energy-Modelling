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

