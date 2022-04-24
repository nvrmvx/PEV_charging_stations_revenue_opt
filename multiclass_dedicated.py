from math import log
import pandas as pd
import random

from simpy import Environment
from simpy.rt import RealtimeEnvironment
from simpy import Resource
from simpy.events import Event

theta1 = 0.75
theta2 = 1-0.75
SOC_I_MU = 0.3
SOC_I_SIGMA = 0.15
P1_MAX = 45
P2_MAX = 22
E_MAX = 15
E1_C = 4
E2_C = 5

BATT_DEG = {"a": 0.004,"b": 0.075,"c": 0.003}

REWARD = {"m": 9,"n": 1}
C_W = 20

T_CH_COEFFICIENT = 2

class Pev:
    def __init__(self, soc_r, i, e_c, p_max, sim: 'Simulation'):
        self.i = i
        soc_i = random.gauss(sim.soc_i_mu,sim.soc_i_sigma)
        soc_i = max(0.05, min(soc_r-0.1, soc_i))
        self.e_i = soc_i*sim.e_max
        self.e_c = e_c
        self.e_r = soc_r*sim.e_max
        self.e_max = sim.e_max
        self.p_max = p_max
        self.sim = sim
        self.sim.temp_pevs.append(
            {
                "pev": i,
                "soc_i": soc_i,
                "charger": 0,
                "arrival_time": None,
                "start_time": None,
                "departure_time": None,
                "mean_power": None,
                "c_batt": None,
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
        p_ow = (self.p_max*t1+(2*m1-n1*(self.e_r+e_i))*t2/2.0)/(t1+t2)
        self.sim.temp_pevs[self.i-1]["mean_power"] = p_ow
        self.sim.temp_pevs[self.i-1]["c_batt"] = self.sim.batt_deg["a"]*p_ow**2+self.sim.batt_deg["b"]*p_ow+self.sim.batt_deg["c"]
        return (t1+t2)*60.0*self.sim.t_ch_coefficient
    
    def go_to_charging_station(self, env, charging_station: 'ChargingStation'):
        # at this point the PEV in question has just pulled up to the charging station
        self.sim.temp_pevs[self.i-1]["arrival_time"] = env.now
        # check if there are any empty spaces near chargers or in the waiting spaces
        if len(charging_station.charger.queue) < charging_station.waiting_space_capacity:
            with charging_station.charger.request() as request:
                yield request
                # at this point the PEV in question is near the charger
                for i in range(1,charging_station.charger.capacity+1):
                    if charging_station.charger_availability[i-1]:
                        self.sim.temp_pevs[self.i-1]["charger"] = i
                        break
                self.sim.temp_pevs[self.i-1]["start_time"] = env.now
                yield env.process(charging_station.charge_pev(self))
        else:
            # at this point the PEV in question has no place to park so it is blocked
            self.sim.temp_pevs[self.i-1]["blocked"] = True
        # at this point the PEV in question is charged and is leaving the charging station
        self.sim.temp_pevs[self.i-1]["departure_time"] = env.now
        if not (charging_station.admission or charging_station.charger.count):
            self.sim.stop_event.succeed()

class ChargingStation:
    def __init__(self, env, s, r):
        self.env = env
        self.charger = Resource(env, s)
        self.charger_availability = list()
        for _ in range(s):
            self.charger_availability.append(True)
        self.waiting_space_capacity = r
        self.admission = True
    
    def charge_pev(self, pev: Pev):
        for i in range(self.charger.capacity):
            if self.charger_availability[i]:
                self.charger_availability[i] = False
                occupied_charger = i
                break
        # wait time until PEV is charged
        yield self.env.timeout(pev.get_charge_time())
        self.charger_availability[occupied_charger] = True

# this is the main class of the simulation
# when it is initialized, the simulation is run automatically

class Simulation:
    def __init__(self,pev_num, lam, s, r1, r2, soc_rs, batt_deg, reward, c_w, t_ch_coefficient, soc_i_mu=SOC_I_MU,soc_i_sigma=SOC_I_SIGMA,p1_max=P1_MAX, p2_max = P2_MAX, e_max=E_MAX,e1_c=E1_C, e2_c = E2_C):
        self.lam = lam
        pev1_num = pev_num*theta1
        pev2_num = pev_num*theta2
        self.pev1_num = pev1_num
        self.s = s
        self.r1 = r1
        self.soc_i_mu = soc_i_mu
        self.soc_i_sigma = soc_i_sigma
        self.p1_max = p1_max
        self.e_max = e_max
        self.e1_c = e1_c
        self.soc_rs=soc_rs
        self.batt_deg = batt_deg
        self.reward = reward
        self.c_w = c_w
        self.t_ch_coefficient = t_ch_coefficient
        self.pevs1 = dict()
        for lam1 in self.lam:
            self.env1 = Environment()
            self.temp_pevs = list()
            self.lam1 = lam1
            self.stop_event = Event(self.env1)
            self.env1.process(self.run_charging_station1())
            self.env1.run(self.stop_event)
            self.temp_pevs = pd.DataFrame(self.temp_pevs)
            self.temp_pevs.set_index("pev", inplace = True)
            self.pevs1[lam1] = self.temp_pevs
        
        self.pev2_num = pev2_num
        self.r2 = r2
        self.soc_i_mu = soc_i_mu
        self.soc_i_sigma = soc_i_sigma
        self.p2_max = p2_max
        self.e_max = e_max
        self.e2_c = e2_c
        self.soc_rs=soc_rs
        self.pevs2 = dict()
        for lam2 in self.lam:
            self.env2 = Environment()
            self.temp_pevs = list()
            self.lam2 = lam2
            self.stop_event = Event(self.env2)
            self.env2.process(self.run_charging_station2())
            self.env2.run(self.stop_event)
            self.temp_pevs = pd.DataFrame(self.temp_pevs)
            self.temp_pevs.set_index("pev", inplace = True)
            self.pevs2[lam2] = self.temp_pevs

    # process function for the simulation to run until a specified number of PEVs is charged
    def run_charging_station1(self):
        charging_station1 = ChargingStation(self.env1, self.s, self.r1)
        i1 = 0
        while True:
            #TODO try a different way of doing this timeout (to mediate the discrepancies with the results from the paper)
            # wait time until next PEV has to be introduced to the simulation
            yield self.env1.timeout(random.expovariate(self.lam1/60))
            i1 += 1
            if charging_station1.admission:
                # create a new PEV in the simulation and send it to the charging station
                pev1 = Pev(self.soc_rs, i1, self.e1_c, self.p1_max, self)
                self.env1.process(pev1.go_to_charging_station(self.env1,charging_station1))
            if i1 >= self.pev1_num:
                charging_station1.admission = False
    
    def run_charging_station2(self):
        charging_station2 = ChargingStation(self.env2, self.s, self.r2)
        i2 = 0
        while True:
            #TODO try a different way of doing this timeout (to mediate the discrepancies with the results from the paper)
            # wait time until next PEV has to be introduced to the simulation
            yield self.env2.timeout(random.expovariate(self.lam2/60))
            i2 += 1
            if charging_station2.admission:
                # create a new PEV in the simulation and send it to the charging station
                pev1 = Pev(self.soc_rs, i2, self.e1_c, self.p2_max, self)
                self.env2.process(pev1.go_to_charging_station(self.env2,charging_station2))
            if i2 >= self.pev2_num:
                charging_station2.admission = False
    
    def get_mean_charging_time1(self):
        #TODO add calculation results too
        temp1 = dict()
        for lam1 in self.lam:
            temp2 = self.pevs1[lam1][self.pevs1[lam1]["blocked"]==False]
            temp1[lam1] = (temp2["departure_time"]-temp2["start_time"]).mean()
        return temp1

    def get_mean_charging_time2(self):
        temp1 = dict()
        for lam2 in self.lam:
            temp2 = self.pevs2[lam2][self.pevs2[lam2]["blocked"]==False]
            temp1[lam2] = (temp2["departure_time"]-temp2["start_time"]).mean()
        return temp1
    
    def get_mean_charging_power1(self):
        #TODO add calculation results too
        temp1 = dict()
        for lam1 in self.lam:
            temp2 = self.pevs1[lam1][self.pevs1[lam1]["blocked"]==False]
            temp1[lam1] = temp2["mean_power"].mean()
        return temp1

    def get_mean_charging_power2(self):
        #TODO add calculation results too
        temp1 = dict()
        for lam2 in self.lam:
            temp2 = self.pevs2[lam2][self.pevs2[lam2]["blocked"]==False]
            temp1[lam2] = temp2["mean_power"].mean()
        return temp1
    
    def get_traffic_intensity1(self):
        #TODO add calculation results too
        temp = dict()
        mu_over_1 = self.get_mean_charging_time1()
        for lam1 in self.lam:
            temp[lam1] = mu_over_1[lam1]*self.lam1/(60*self.s)
        return temp
    
    def get_traffic_intensity2(self):
        #TODO add calculation results too
        temp = dict()
        mu_over_1 = self.get_mean_charging_time2()
        for lam2 in self.lam:
            temp[lam2] = mu_over_1[lam2]*self.lam2/(60*self.s)
        return temp
    
    def get_blocking_probability1(self):
        #TODO add calculation results too
        temp1 = dict()
        for lam1 in self.lam:
            temp1[lam1] = len(self.pevs1[lam1][self.pevs1[lam1]["blocked"]==True].index)/len(self.pevs1[lam1].index)
        return temp1

    def get_blocking_probability2(self):
        #TODO add calculation results too
        temp2 = dict()
        for lam2 in self.lam:
            temp2[lam2] = len(self.pevs2[lam2][self.pevs2[lam2]["blocked"]==True].index)/len(self.pevs2[lam2].index)
        return temp2
    
    def get_mean_waiting_time1(self):
        #TODO add calculation results too
        temp1 = dict()
        for lam1 in self.lam:
            temp2 = self.pevs1[lam1][self.pevs1[lam1]["blocked"]==False]
            temp1[lam1] = (temp2["start_time"]-temp2["arrival_time"]).mean()
        return temp1

    def get_mean_waiting_time2(self):
        #TODO add calculation results too
        temp1 = dict()
        for lam2 in self.lam:
            temp2 = self.pevs2[lam2][self.pevs2[lam2]["blocked"]==False]
            temp1[lam2] = (temp2["start_time"]-temp2["arrival_time"]).mean()
        return temp1
    
    def get_system_revenue1(self):
        #TODO add calculation results too
        temp1 = dict()
        reward = lambda x: self.reward["m"]*x+self.reward["n"]
        p_k = self.get_blocking_probability1()
        mean_t_w = self.get_mean_waiting_time1()
        mean_t_ch = self.get_mean_charging_time1()
        for lam1 in self.lam:
            temp2 = self.pevs1[lam1][self.pevs1[lam1]["blocked"]==False]
            mean_c_batt = temp2["c_batt"].mean()
            temp1[lam1] = self.lam1*(1-p_k[lam1])*(reward(lam1)-self.c_w*mean_t_w[lam1]/60.0-mean_c_batt*mean_t_ch[lam1]/60.0)
        return temp1

    def get_system_revenue2(self):
        #TODO add calculation results too
        temp1 = dict()
        reward = lambda x: self.reward["m"]*x+self.reward["n"]
        p_k = self.get_blocking_probability2()
        mean_t_w = self.get_mean_waiting_time2()
        mean_t_ch = self.get_mean_charging_time2()
        for lam2 in self.lam:
            temp2 = self.pevs2[lam2][self.pevs2[lam2]["blocked"]==False]
            mean_c_batt = temp2["c_batt"].mean()
            temp1[lam2] = self.lam2*(1-p_k[lam2])*(reward(lam2)-self.c_w*mean_t_w[lam2]/60.0-mean_c_batt*mean_t_ch[lam2]/60.0)
        return temp1

    def get_results1(self):
        return self.pevs1

    def get_results2(self):
        return self.pevs2

if __name__ == "__main__":
    #? env = RealtimeEnvironment(factor=0.1,strict=False)
    sim = Simulation(
        pev_num=500,
        lam=[1, 2, 3, 4, 5, 6, 7],
        s=10,
        r1=3,
        r2=3,
        soc_rs=0.9,
        batt_deg=BATT_DEG,
        reward=REWARD,
        c_w=C_W,
        t_ch_coefficient=T_CH_COEFFICIENT
    )

    print(sim.get_results1())
    print(sim.get_mean_charging_time1())
    print(sim.get_mean_charging_power1())
    print(sim.get_traffic_intensity1()) #! does not work yet
    print(sim.get_blocking_probability1())
    print(sim.get_mean_waiting_time1())
    print(sim.get_system_revenue1()) #! does not work yet

    print(sim.get_results2())
    print(sim.get_mean_charging_time2())
    print(sim.get_mean_charging_power2())
    print(sim.get_traffic_intensity2()) #! does not work yet
    print(sim.get_blocking_probability2())
    print(sim.get_mean_waiting_time2())
    print(sim.get_system_revenue2()) #! does not work yet
    #TODO add a graphing algorithm to compare it with the paper's results