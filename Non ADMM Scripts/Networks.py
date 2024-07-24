import matplotlib.pyplot as plt
import gurobipy as gp
class Network:

    def __init__(self, T, model, Econnections,  name = None):
        """Initialize a new Terminal object. """
        self.T = T,
        self.Econnections = Econnections
        self.name = "Line" if name is None else name
        self.model = model
        self.dual = [0]*len(T)

        for Econnection in Econnections:
            Econnection.set_network(self)

        self.setConstraints()

    def setConstraints(self):
        """Sets the constraints of the optimization model"""
        self.constraints = []
        for t in self.T[0]:
            constraint = self.model.addConstr(
                gp.quicksum(Econnection.powerVariables[t] for Econnection in self.Econnections) == 0,
                name=f"sum_zero_constraint_{t}"
            )
            self.constraints.append(constraint)
        self.model.update()

    def deleteConstraints(self):
        """Deletes all the constraints of the optimization model"""
        for constraint in self.constraints:
            self.model.remove(constraint)
        self.model.update()
        self.constraints = []

    def addEconnection(self, Econnection):
        """Adds an Econnection to the network and updates the constraints"""
        self.Econnections.append(Econnection)
        Econnection.set_network(self)
        self.deleteConstraints()
        self.setConstraints()

    def removeEconnection(self, Econnection):
        """Removes an Econnection from the network and updates the constraints"""
        if Econnection in self.Econnections:
            self.Econnections.remove(Econnection)
            self.deleteConstraints()
            self.setConstraints()


    def updateDual(self):
        """Returns a list of dual values for each time period"""
        duals = []
        for t in self.T[0]:
            duals.append(self.constraints[t].Pi)
        self.dual = duals
    
    def plotData(self):
        months = ["25 Mar", "26 Mar", "27 Mar","28 Mar", "29 Mar", "30 Mar", "31 Mar", "01 Apr", "02 Apr", "03 Apr", "04 Apr", "05 Apr", "06 Apr", ]
        x_ticks = [i * (24) for i in range(13)]

        # Plot data
        plt.figure(figsize=(15, 8))

        for c in self.Econnections:
            plt.plot(c.powerValues[1992:2282], label=f'{c.device.name }')

        plt.xticks(ticks=x_ticks, labels=months)
        
        plt.grid(which='both', linestyle='--', linewidth=0.5)
        # plt.gca().xaxis.set_major_locator(plt.MultipleLocator(760))
        plt.xlabel("Time",fontsize=14)
        plt.ylabel("Power subtracted from the network [MWh]",fontsize=14)
        plt.title(f"Device Power Usage",fontsize=16)
        plt.legend(fontsize=12)

        plt.savefig('distribution_plot.png', dpi=300)

        plt.show()

#########################################################################################################################################

class ThermalNetwork:
    def __init__(self, T,  Hconnections, model, name = None):
        """Initialize a new Terminal object. """
        self.T = T, 
        self.Hconnections = Hconnections
        self.name = "Pipe" if name is None else name
        self.dual = [0]*len(T)
        self.model = model
        for Hconnection in Hconnections:
            Hconnection.set_network(self)
        
        self.setConstraints()


    def setConstraints(self):
        """Sets the constraints of the optimization model"""
        self.model.addConstrs(
            (gp.quicksum(Hconnection.heatVariables[t] for Hconnection in self.Hconnections) == 0 for t in self.T),
            name="sum_zero_constraint"
        )
        self.model.update()

    def updateDual(self):
        """Returns a list of dual values for each time period"""
        duals = []
        for t in self.T[0]:
            duals.append(self.constraints[t].Pi)
        self.dual = duals

    def plotData(self):
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            x_ticks = [i * (730)+ 365 for i in range(12)]
            # Plot data
            plt.figure(figsize=(15, 8))

            for c in self.Hconnections:
                plt.plot(c.heatValues, label=f'{c.device.name}')

            plt.xticks(ticks=x_ticks, labels=months)
            plt.grid(which='both', linestyle='--', linewidth=0.5)
            # plt.gca().xaxis.set_major_locator(plt.MultipleLocator(760))
            plt.xlabel("Month",fontsize=12)
            plt.ylabel("Power subtracted from the network",fontsize=14)
            plt.title(f"Device Power Usage on {self.name}",fontsize=16)
            plt.legend()
            plt.show()