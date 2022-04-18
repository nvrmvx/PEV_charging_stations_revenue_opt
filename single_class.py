from math import log
import pandas as pd
import random

from simpy import Environment
from simpy.rt import RealtimeEnvironment
from simpy import Resource
from simpy.events import Event

BATT_DEG_A = 0.004
BATT_DEG_B = 0.075
BATT_DEG_C = 0.003

#! the reward might be SoC_r-SoC_i instead of just SoC_r
REWARD_M = 9 #! the paper says that it is calculated from price (but it is not)
REWARD_N = 1
C_W = 20

SOC_I_MU = 0.3
SOC_I_SIGMA = 0.15
P_MAX = 45
E_MAX = 15
E_C = 5

class Pev:
    def __init__(self, soc_i_mu, soc_i_sigma, p_max, e_max, e_c, soc_r, i, sim: 'Simulation'):
        self.i = i
        soc_i = random.gauss(soc_i_mu,soc_i_sigma)
        soc_i = max(0.05, min(soc_r-0.1, soc_i))
        self.e_i = soc_i*e_max
        self.e_c = e_c
        self.e_r = soc_r*e_max
        self.e_max = e_max
        self.p_max = p_max
        self.sim = sim
        self.sim.pevs.append(
            {
                "soc_i": soc_i,
                "mean_power": None,
                "arrival_time": None,
                "start_time": None,
                "departure_time": None,
                "blocked": False
            }
        )
    
    #! there is an assumption that e_r is never lower than e_c
    def get_charge_time(self):
        n1 = self.p_max/(self.e_max-self.e_c)
        m1 = n1*self.e_c + self.p_max
        e_i = self.e_i
        t1 = 0.0
        if e_i <= self.e_c:
            t1 = (self.e_c-e_i)/self.p_max
            e_i = self.e_c
        t2 = log((m1-n1*e_i)/(m1-n1*self.e_r),10.0)/n1
        self.sim.pevs[self.i-1]["mean_power"] = (self.p_max*t1+(self.p_max+m1-n1*self.e_r)*t2/2.0)/(t1+t2)
        return (t1+t2)*60.0
    
    def go_to_charging_station(self, env, charging_station: 'ChargingStation'):
        # at this point the PEV in question has just pulled up to the charging station
        self.sim.pevs[self.i-1]["arrival_time"] = env.now
        # check if there are any empty spaces near chargers or in the waiting spaces
        if len(charging_station.charger.queue) < charging_station.waiting_space_capacity:
            with charging_station.charger.request() as request:
                yield request
                # at this point the PEV in question is near the charger
                self.sim.pevs[self.i-1]["start_time"] = env.now
                yield env.process(charging_station.charge_pev(self))
        else:
            # at this point the PEV in question has no place to park so it is blocked
            self.sim.pevs[self.i-1]["blocked"] = True
        # at this point the PEV in question is charged and is leaving the charging station
        self.sim.pevs[self.i-1]["departure_time"] = env.now

class ChargingStation:
    def __init__(self, env, s, r):
        self.env = env
        self.charger = Resource(env, s)
        self.waiting_space_capacity = r
    
    def charge_pev(self, pev: Pev):
        # wait time until PEV is charged
        yield self.env.timeout(pev.get_charge_time())

# this is the main class of the simulation
# when it is initialized, the simulation is run automatically
class Simulation:
    def __init__(self,env,pev_num,lam,s,r,soc_r,soc_i_mu=SOC_I_MU,soc_i_sigma=SOC_I_SIGMA,p_max=P_MAX,e_max=E_MAX,e_c=E_C):
        self.env = env
        self.pev_num = pev_num
        self.lam = lam
        self.s = s
        self.r = r
        self.soc_i_mu = soc_i_mu
        self.soc_i_sigma = soc_i_sigma
        self.p_max = p_max
        self.e_max = e_max
        self.e_c = e_c
        self.soc_r=soc_r
        self.pevs = list()
        stop_event = Event(env)
        env.process(self.run_charging_station(stop_event=stop_event))
        self.env.run(stop_event)
        self.pevs = pd.DataFrame(self.pevs)

    # process function for the simulation to run until a specified number of PEVs is charged
    def run_charging_station(self, stop_event):
        charging_station = ChargingStation(self.env, self.s, self.r)
        admission = True
        i = 0
        while True:
            #TODO try a different way of doing this timeout (to mediate the discrepancies with the results from the paper)
            # wait time until next PEV has to be introduced to the simulation
            yield self.env.timeout(random.expovariate(self.lam/60))
            i += 1
            if admission:
                # create a new PEV in the simulation and send it to the charging station
                pev = Pev(self.soc_i_mu, self.soc_i_sigma, self.p_max, self.e_max, self.e_c, self.soc_r, i, self)
                self.env.process(pev.go_to_charging_station(self.env,charging_station))
            if i >= self.pev_num:
                # wait until all PEVs that are smaller than or equal to pev_num are charged and stop simulation
                admission = False
                if charging_station.charger.count == 0:
                    stop_event.succeed()
    
    def get_mean_charging_time(self):
        #TODO add calculation results too
        temp = self.pevs[self.pevs["blocked"]==False]
        return (temp["departure_time"]-temp["start_time"]).mean()
    
    def get_mean_charging_power(self):
        #TODO add calculation results too
        temp = self.pevs[self.pevs["blocked"]==False]
        return temp["mean_power"].mean()
    
    def get_traffic_intensity(self):
        #TODO add calculation results too
        #TODO finish this
        return
    
    def get_blocking_probability(self):
        #TODO add calculation results too
        return len(self.pevs[self.pevs["blocked"]==True].index)/len(self.pevs.index)
    
    def get_mean_waiting_time(self):
        #TODO add calculation results too
        temp = self.pevs[self.pevs["blocked"]==False]
        return (temp["start_time"]-temp["arrival_time"]).mean()
    
    def get_system_revenue(self):
        #TODO add calculation results too
        #TODO finish this
        return

    def get_results(self):
        return(self.pevs)

if __name__ == "__main__":
    #? env = RealtimeEnvironment(factor=0.1,strict=False)
    env = Environment()
    sim = Simulation(
        env=env,
        pev_num=500,
        lam=10,
        s=7,
        r=3,
        soc_r=0.95
    )
    print(sim.get_results())
    print(sim.get_mean_charging_time())
    print(sim.get_mean_charging_power())
    print(sim.get_traffic_intensity()) #! does not work yet
    print(sim.get_blocking_probability())
    print(sim.get_mean_waiting_time())
    print(sim.get_system_revenue()) #! does not work yet
    #TODO add a graphing algorithm to compare it with the paper's results