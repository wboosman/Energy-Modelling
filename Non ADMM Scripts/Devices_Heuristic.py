import numpy as np 
import gurobipy as gp 
from gurobipy import GRB
import pandas as pd
from Connections_NA import EConnection, HConnection


class HeuristicDevice:
    def __init__(self, T, model, net_from, net_to=None, Econnections = None, Hconnections=None, name=None):
        self.name = type(self).__name__ if name is None else name
        self.Econnections = Econnections
        self.Hconnections = Hconnections
        self.model = model
        self.net_from = net_from
        self.net_to = net_to
        self.model.setParam('OutputFlag', 0)
        self._investment_cost = 0
        if Econnections is not None: 
            for Econnection in Econnections:
                Econnection._init_problem(self.model, len(T))
                Econnection.set_device(self)

        if Hconnections is not None: 
            for Hconnection in Hconnections:
                Hconnection._init_problem(self.model, len(T))
                Hconnection.set_device(self)

    
    @property
    def investment_cost(self):
        """Getter method for the cost property"""
        return self._investment_cost

    @investment_cost.setter
    def investment_cost(self, value):
        """Setter method for the cost property"""
        self._investment_cost = value

    
    def getModel(self):
        return self.model
    

#########################################################################################################################################

class HeuristicRenewable(HeuristicDevice):
    def __init__(
        self,
        T,
        model,
        net_from,
        price_list,
        technology = None,
        install_cap = None,
        name=None,
    ):
        super(HeuristicRenewable, self).__init__(T, model, net_from, Econnections=[EConnection()], name=f"Renewable {technology}")
        self.T = T
        self.technology = technology
        self.power_min = 0
        self.install_cap = install_cap
        self.power_available = self.determinePowerGeneration()
        self.price_list= price_list
        self.investment_cost = price_list[technology][install_cap]

        self.setConstraints()


    def determinePowerGeneration(self):
        df = pd.read_excel('Renewable_potential.xlsx')
        if self.technology == 'Wind':
            column_name = 'Wind_potential'
        elif self.technology == 'PV':
            column_name  = 'PV_potential'
        else:
            print("No valid technology")
        normalized_power_potential = df[column_name].tolist()
        # Calculate real power based on normalized load profile and annual power demand
        real_power = [x * self.install_cap for x in normalized_power_potential]
        return real_power
    
    def setConstraints(self):
        """Sets the constraints of the optimization model"""
        powerVar = self.Econnections[0].powerVariables

        # When there is a dissipation device available
        self.model.addConstrs(-powerVar[t] == self.power_available[t] for t in self.T)   

        # When there is not
        # self.model.addConstrs(-powerVar[t] <=  self.z * self.power_available[t] for t in self.T)
        # self.model.addConstrs(-powerVar[t] >=  self.power_min for t in self.T) 


    
    
#########################################################################################################################################

class HeuristicTransmissionLine(HeuristicDevice):
    def __init__(self, T, model, net_from, net_to, price_list, length,  power_max=None, alpha=None ,  name='Transmission Line'):
        super(HeuristicTransmissionLine, self).__init__(T, model, net_from, net_to, Econnections= [EConnection(), EConnection()], name= name)
        self.T = T
        self.power_max = power_max
        self.alpha = alpha
        self.length = length
        self.investment_cost = price_list['Transmission'][length][power_max]
        
        if self.alpha is not None:
            self._updateObjective()
        self.setConstraints()

    def _updateObjective(self):
        powerVar   = self.Econnections[0].powerVariables
        self.objective  = gp.quicksum(self.alpha * (powerVar[t] * powerVar[t])  for t in self.T)
        self.model.setObjective(self.model.getObjective() + self.objective, gp.GRB.MINIMIZE)
        self.model.update()

    def setConstraints(self):
        """Sets the constraints of the optimization model"""
        powerVar_1 = self.Econnections[0].powerVariables
        powerVar_2 = self.Econnections[1].powerVariables

        self.model.addConstrs(powerVar_1[t] + powerVar_2[t] ==  0 for t in self.T)
        if self.power_max is not None:
            self.model.addConstrs((powerVar_1[t] - powerVar_2[t]) / 2 <= self.power_max for t in self.T)
            self.model.addConstrs((powerVar_2[t] - powerVar_1[t]) / 2 <= self.power_max for t in self.T)


    
#########################################################################################################################################

class HeuristicStorage(HeuristicDevice):
    def __init__(
        self,
        T,
        model,
        net_from,
        price_list,
        discharge_max=None,
        charge_max=None,
        energy_final=None,
        energy_max=None,
        name='Storage',
        final_energy_price=None,
    ):
        super().__init__(T,model, net_from, Econnections=[EConnection()], name=name)
        self.T = T
        self.discharge_max = discharge_max
        self.charge_max = charge_max
        self.energy_init = 0
        self.energy_max = energy_max
        self.energy_final = energy_final
        self.final_energy_price = final_energy_price
        self.energy = None
        self.investment_cost = price_list['Storage'][energy_max]

        self.setVariables()
        self.setConstraints()


    def setConstraints(self):
        """Sets the constraints of the optimization model"""
        powerVar = self.Econnections[0].powerVariables

        if self.discharge_max is not None: 
            self.model.addConstrs(powerVar[t] >= -self.discharge_max for t in self.T ) 

        if self.charge_max is not None: 
            self.model.addConstrs(powerVar[t] <= self.charge_max for t in self.T ) 

        self.model.addConstr(self.energy[0] == self.energy_init + powerVar[0] ) 
        self.model.addConstrs(self.energy[t] - self.energy[t-1]  ==  powerVar[t] for t in self.T if t>0)
        
        
        self.model.addConstrs(self.energy[t] >= 0 for t in self.T ) 
        self.model.addConstrs(self.energy[t] <= self.energy_max for t in self.T ) 

    def setVariables(self):
        """Sets the Variables of the optimization model"""
        self.energy = self.model.addVars(self.T)

    

