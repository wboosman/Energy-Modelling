import numpy as np 
import gurobipy as gp 
import pandas as pd
from Connections_NA import EConnection



class Device:
    def __init__(self, T, model, Econnections = None, name=None):
        self.name = type(self).__name__ if name is None else name
        self.Econnections = Econnections
        self.model = model
        if Econnections is not None: 
            for Econnection in Econnections:
                Econnection._init_problem(self.model, len(T))
                Econnection.set_device(self)



    def totalPayment(self):
        """Network optimization results. Print here the power output and the payment scheme"""
        total_sum = 0
        if self.Econnections is not None: 
            for connection in self.Econnections:
                total_sum += connection.getTotalPayment()
        return total_sum
    
    def hourlyPayment(self):
        """Network optimization results. Print here the power output and the payment scheme"""
        hourlyPayment = [0] * len(self.Econnections[0].getHourlyPayment())
        if self.Econnections is not None: 
            for c in self.Econnections:
                hourlyPay = c.getHourlyPayment()
                hourlyPayment = [sum_val + hourlyPay for sum_val, hourlyPay in zip(hourlyPayment, hourlyPay)]     
        return hourlyPayment

#########################################################################################################################################

class CHP(Device):
    def __init__(
        self,
        T,
        model,
        power_max=None,
        power_min = 0,
        ramp_min=None,
        ramp_max=None,
        operating_point = None,
        power_init=None,
        alpha=0,
        beta=0,
        gamma=0,
        name= 'CHP',
    ):
        super().__init__(T, model, Econnections=[EConnection(), EConnection()], name=name)
        self.T = T
        self.power_max = power_max
        self.power_min = power_min
        self.ramp_min = ramp_min
        self.ramp_max = ramp_max
        self.power_init = power_init
        self.operating_point = operating_point
        self.alpha = alpha
        self.beta= beta
        self.gamma = gamma
        self.boiler = None

        self.setVariables()
        self._updateObjective()
        self.setConstraints()


    def _updateObjective(self):
        powerVar = self.Econnections[0].powerVariables
        #set new variable, fuel burned for heat call it q

        self.objective  = gp.quicksum(self.alpha * ((-powerVar[t] - self.operating_point) * (-powerVar[t] - self.operating_point)) - self.beta * powerVar[t] + self.gamma for t in self.T)          #+ self.beta_q * heatVar[t] + self.gamma_q  for t in self.T)
        self.objective  += gp.quicksum( -(self.beta/2) * self.boiler[t]  for t in self.T)  
        self.model.setObjective(self.model.getObjective() + self.objective, gp.GRB.MINIMIZE)
        self.model.update()

    def setConstraints(self):
        """Sets the constraints of the optimization model"""
        powerVar = self.Econnections[0].powerVariables
        heatVar = self.Econnections[1].powerVariables

        self.model.addConstrs(-powerVar[t] -(1/2)*self.boiler[t] <=  self.power_max for t in self.T)

        self.model.addConstrs(-powerVar[t]    >= self.power_min for t in self.T) 
        self.model.addConstrs(-self.boiler[t] >=  self.power_min for t in self.T) 

        # With dissipation
        self.model.addConstrs(heatVar[t] ==  powerVar[t] + self.boiler[t] for t in self.T)

        if self.ramp_max is not None: 
            self.model.addConstrs(-powerVar[t] + powerVar[t-1] <=  self.ramp_max for t in self.T if t>0)
            self.model.addConstrs((-1/2) * self.boiler[t] + (1/2) * self.boiler[t-1] <=  self.ramp_max for t in self.T if t>0)
        
        if self.ramp_min is not None:
            self.model.addConstrs(-powerVar[t] + powerVar[t-1]  >=  self.ramp_min for t in self.T if t>0)
            # No need for ramping for heat, you can always shed
            self.model.addConstrs((-1/2)*self.boiler[t]  + (1/2)*self.boiler[t-1] >=  self.ramp_min for t in self.T if t>0)

        if self.power_init is not None:
            self.model.addConstr(-powerVar[0] == self.power_init)  

        self.model.update()

    def setVariables(self):
        """Sets the Variables of the optimization model"""
        self.boiler = self.model.addVars(self.T, lb = -100)
        self.model.update()

    def getTotalOpex(self):
        elec_opex = sum(self.alpha * x * x- self.beta * x + self.gamma  for x in self.Econnections[0].powerValues)
        heat_opex = sum((-self.beta/2) * var.x for var in self.boiler.values())
        total_sum = elec_opex + heat_opex
        return total_sum

    def getHourlyOpex(self):
        hourly_elec_opex = [self.alpha * x * x- self.beta * x + self.gamma for x in self.Econnections[0].powerValues]
        hourly_heat_opex = [(-1/2)* self.beta * var.x  for var in self.boiler.values()]
        hourly_opex  = [x + y for x, y in zip(hourly_elec_opex, hourly_heat_opex)]
        return hourly_opex



#########################################################################################################################################

class Generator(Device):
    def __init__(
        self,
        T,
        model,
        power_min=None,
        power_max=None,
        ramp_min=None,
        ramp_max=None,
        power_init=None,
        operating_point = None,
        alpha=0,
        beta=0,
        gamma=0,
        name='Generator',
    ):
        super().__init__(T, model,[EConnection()], name= name)
        self.T = T
        self.power_min = power_min
        self.power_max = power_max
        self.ramp_min = ramp_min
        self.ramp_max = ramp_max
        self.power_init = power_init
        self.operating_point = operating_point
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.objective = None

        # self.setVariables()
        self._updateObjective()
        self.setConstraints()

    def _updateObjective(self):
        powerVar   = self.Econnections[0].powerVariables
        self.objective  = gp.quicksum(self.alpha * ((-powerVar[t] - self.operating_point) * (-powerVar[t] - self.operating_point)) - self.beta * powerVar[t] + self.gamma for t in self.T)
        self.model.setObjective(self.model.getObjective() + self.objective, gp.GRB.MINIMIZE)
        self.model.update()


    def setConstraints(self):
        """Sets the constraints of the optimization model"""
        powerVar = self.Econnections[0].powerVariables

        self.model.addConstrs(-powerVar[t] <=  self.power_max for t in self.T)
        self.model.addConstrs(-powerVar[t] >=  self.power_min for t in self.T) 

        if self.ramp_max is not None: 
            self.model.addConstrs(-powerVar[t] + powerVar[t-1]  <=  self.ramp_max for t in self.T if t>0)
        if self.ramp_min is not None:
            self.model.addConstrs(-powerVar[t] + powerVar[t-1]  >=  self.ramp_min for t in self.T if t>0)
        if self.power_init is not None:
            self.model.addConstr(-powerVar[0] == self.power_init)  

    def setVariables(self):
        """Sets the Variables of the optimization model"""
        pass


    def getTotalOpex(self):
        total_sum = sum(self.alpha * x * x- self.beta * x + self.gamma for x in self.Econnections[0].powerValues)
        return total_sum

    def getHourlyOpex(self):
        hourly_opex = [self.alpha * x * x- self.beta * x + self.gamma for x in self.Econnections[0].powerValues]
        return hourly_opex

#########################################################################################################################################

class Renewable(Device):
    def __init__(
        self,
        T,
        model,
        technology = None,
        install_cap = None,
        name=None,
    ):
        super(Renewable, self).__init__(T, model,[EConnection()], name=f"Renewable {technology}")
        self.T = T
        self.technology = technology
        self.power_min = 0
        self.install_cap = install_cap
        self.power_available = self.determinePowerGeneration()

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

        # With Power Dissipation
        self.model.addConstrs(-powerVar[t] ==  self.power_available[t] for t in self.T)
        
        # Without Power Dissipation
        # self.model.addConstrs(-powerVar[t] <=  self.power_available[t] for t in self.T)
        # self.model.addConstrs(-powerVar[t] >=  self.power_min for t in self.T) 

        

#########################################################################################################################################

class FixedLoad(Device): 
    def __init__(
        self,
        T,
        model,
        buildingType = None, 
        annualDemand = None,
        name = 'Electrical Load',
    ):
        super(FixedLoad, self).__init__(T, model,[EConnection()], name=name)
        self.T = T
        self.buildingType = buildingType
        self.annualDemand = annualDemand
        self.power = self.determineLoadProfile()
        assert all(item > 0 for item in self.power)

        self.setConstraints()

    def determineLoadProfile(self):
        df = pd.read_excel('load_profiles_normalized.xlsx')
        normalized_power = df[self.buildingType].tolist()
        # Calculate real power based on normalized load profile and annual power demand
        real_power = [x * self.annualDemand for x in normalized_power]
        return real_power
    
    def setConstraints(self):
        """Sets the constraints of the optimization model"""
        powerVar = self.Econnections[0].powerVariables

        self.model.addConstrs(powerVar[t] ==  self.power[t] for t in self.T)
    
#########################################################################################################################################

class ThermalLoad(Device): 
    def __init__(
        self,
        T,
        model,
        heatingType = None, 
        numberHouseholds = None,
        name = 'Thermal Load',
    ):
        super(ThermalLoad, self).__init__(T,model, [EConnection()], name=name)
        self.T = T
        self.heatingType = heatingType
        self.numberHouseholds = numberHouseholds
        self.power = self.determineLoadProfile()
        assert all(item >= 0 for item in self.power)
        assert self.heatingType in ['HP', 'Heating']

        self.setConstraints()

    def determineLoadProfile(self):
        df = pd.read_excel('ThermalLoadHousehold.xlsx')
        ThermalDemand = df[self.heatingType].tolist()
        # Calculate real power based on normalized load profile and annual power demand
        real_demand = [x * self.numberHouseholds for x in ThermalDemand]
        return real_demand
    
    def setConstraints(self):
        """Sets the constraints of the optimization model"""
        powerVar = self.Econnections[0].powerVariables

        self.model.addConstrs(powerVar[t] ==  self.power[t] for t in self.T)
    

#########################################################################################################################################

class TransmissionLine(Device):
    def __init__(self, T, model, power_max=None, alpha=None, name='Transmission Line'):
        super(TransmissionLine, self).__init__(T, model, [EConnection(), EConnection()], name= name)
        self.T = T
        self.power_max = power_max
        self.alpha = alpha 

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

class Storage(Device):
    def __init__(
        self,
        T,
        model,
        discharge_max=None,
        charge_max=None,
        energy_final=None,
        energy_max=None,
        name='Storage',
        final_energy_price=None,
    ):
        super().__init__(T,model, Econnections=[EConnection()], name=name)
        self.T = T
        self.discharge_max = discharge_max
        self.charge_max = charge_max
        self.energy_init = 0
        self.energy_max = energy_max
        self.energy_final = energy_final
        self.final_energy_price = final_energy_price
        self.energy = None
        
        self.setVariables()
        self.setConstraints()


    def setConstraints(self):
        """Sets the constraints of the optimization model"""
        powerVar = self.Econnections[0].powerVariables

        if self.discharge_max is not None: 
            self.model.addConstrs(powerVar[t] >= -self.discharge_max for t in self.T ) 

        if self.charge_max is not None: 
            self.model.addConstrs(powerVar[t] <= self.charge_max for t in self.T ) 

        self.model.addConstr(self.energy[0] == self.energy_init + powerVar[0]) 
        self.model.addConstrs(self.energy[t] - self.energy[t-1]  ==  powerVar[t] for t in self.T if t>0)
        
        
        self.model.addConstrs(self.energy[t] >= 0 for t in self.T ) 
        self.model.addConstrs(self.energy[t] <= self.energy_max for t in self.T ) 

    def setVariables(self):
        """Sets the Variables of the optimization model"""
        self.energy = self.model.addVars(self.T)



#########################################################################################################################################

class PowerDissipation(Device):
    def __init__(
        self, T, model, name=None
    ):
        super().__init__(T, model,Econnections=[EConnection()], name=name)
        self.T = T
        self.setConstraints()

    def setConstraints(self):
        """Sets the constraints of the optimization model"""
        powerVar = self.Econnections[0].powerVariables
        self.model.addConstrs(powerVar[t] >= 0  for t in self.T)


    
#########################################################################################################################################

class HeatDissipation(Device):
    def __init__(
        self, T, model, name=None
    ):
        super().__init__(T, model,Econnections=[EConnection()], name=name)
        self.T = T
        self.setConstraints()

    def setConstraints(self):
        """Sets the constraints of the optimization model"""
        heatVar = self.Econnections[0].powerVariables
        self.model.addConstrs(heatVar[t] >= 0  for t in self.T)

#########################################################################################################################################

class ExternalPower(Device):
    def __init__(
        self, T,model, price,  name=None
    ):
        super().__init__(T,model, Econnections=[EConnection()], name=name)
        self.T = T
        self.price = price
        self._updateObjective()
        self.setConstraints()

    def _updateObjective(self):
        powerVar   = self.Econnections[0].powerVariables
        self.objective  = gp.quicksum(-self.price * powerVar[t] for t in self.T)
        self.model.setObjective(self.model.getObjective() + self.objective, gp.GRB.MINIMIZE)
        self.model.update()


    def setConstraints(self):
        """Sets the constraints of the optimization model"""
        powerVar = self.Econnections[0].powerVariables
        self.model.addConstrs(powerVar[t] <= 0  for t in self.T)
    
    def getTotalOpex(self):
        total_sum = sum(-self.price * x for x in self.Econnections[0].powerValues)
        return total_sum

    def getHourlyOpex(self):
        hourly_opex = [-self.price * x for x in self.Econnections[0].powerValues]
        return hourly_opex

#########################################################################################################################################

class FixedLoadTest(Device):
    def __init__(
        self, T,model, power=None, name=None
    ):
        super().__init__(T, model,[EConnection()], name)
        self.T = T
        self.power = power
        self.setConstraints()

    def setConstraints(self):
        """Sets the constraints of the optimization model"""
        powerVar = self.Econnections[0].powerVariables
        self.model.addConstrs(powerVar[t] ==  self.power[t] for t in self.T)
