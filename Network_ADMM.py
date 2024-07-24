import matplotlib.pyplot as plt

class Network:

    def __init__(self, T, Econnections, name = None):
        """Initialize a new Terminal object. """
        self.Econnections = Econnections
        self.name = "Line" if name is None else name
        self.dual = [0]*len(T)
        self.balance = [0]*len(T)
        for Econnection in Econnections:
            Econnection.set_network(self)
        

    def updateBalance(self):
        """This function updates the balance betwen the two incoming power flows on the line"""
        #This loss part is new and still in test phase 
        zipped_powers = zip(*(Econnection.powerValues for Econnection in self.Econnections))
        self.balance  = [sum(powers) / len(powers) for powers in zipped_powers]
        #This balance phase was just average is now average - loss -> balance will allways be a bit shifted

    def updateDual(self):
        """This function updates the dual variable of the line by adding the imbalance to the previous dual variable """
        self.dual = [x + y for x, y in zip(self.dual, self.balance)]

    def plotData(self):
        # months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        # x_ticks = [i * (730)+ 365 for i in range(12)]

        # Plot data
        plt.figure(figsize=(15, 8))

        for c in self.Econnections:
            plt.plot(c.powerValues, label=f'{c.device.name }')

        # plt.xticks(ticks=x_ticks, labels=months)
        
        plt.grid(which='both', linestyle='--', linewidth=0.5)
        # plt.gca().xaxis.set_major_locator(plt.MultipleLocator(760))
        plt.xlabel("Month")
        plt.ylabel("Power subtracted from the network")
        plt.title(f"Device Power Usage on {self.name}")
        plt.legend()

        plt.show()

#########################################################################################################################################

class ThermalNetwork:
    def __init__(self, T,  Hconnections, name = None):
        """Initialize a new Terminal object. """
        self.Hconnections = Hconnections
        self.name = "Pipe" if name is None else name
        self.dual =  [0]*len(T)
        self.balance =  [0]*len(T)
        for Hconnection in Hconnections:
            Hconnection.set_network(self)

    def updateBalance(self):
        """This function updates the balance betwen the two incoming power flows on the line"""
        #This loss part is new and still in test phase 
        zipped_thermal = zip(*(Hconnection.heatValues for Hconnection in self.Hconnections))
        self.balance  = [sum(thermal_energy) / len(thermal_energy) for thermal_energy in zipped_thermal]

    def updateDual(self):
        """This function updates the dual variable of the line by adding the imbalance to the previous dual variable """
        self.dual = [x + y for x, y in zip(self.dual, self.balance)]

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
            plt.xlabel("Month")
            plt.ylabel("Power subtracted from the network")
            plt.title(f"Device Power Usage on {self.name}")
            plt.legend()
            plt.show()