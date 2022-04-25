from math import (log,sqrt,exp,factorial)
import pandas as pd
import random

from simpy import Environment
from simpy import Resource
from simpy.events import Event

PEV_NUM = 500
LAM = 10.0
S = 7
R = 3
SOC_RS = [0.60, 0.65, 0.70, 0.75, 0.80,0.85,0.90,0.95,0.99]

BATT_DEG = {"a": 0.004,"b": 0.075,"c": 0.003}

REWARD = {"m": 9,"n": 1}
C_W = 20

SOC_I_P = {"mu": 0.3,"sigma": 0.15}
P_MAX = 45
E_MAX = 15
E_C = 5

T_CH_COEFFICIENT = 2

class Pev:
    def __init__(self, soc_r, i, sim: 'Simulation'):
        self.i = i
        soc_i = random.gauss(sim.soc_i_mu,sim.soc_i_sigma)
        soc_i = max(0.05, min(soc_r-0.1, soc_i))
        self.e_i = soc_i*sim.e_max
        self.e_c = sim.e_c
        self.e_r = soc_r*sim.e_max
        self.e_max = sim.e_max
        self.p_max = sim.p_max
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
        #! only multiplying by 2 gives the graphs from the paper
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
    def __init__(self,pev_num,lam,s,r,soc_rs,soc_i_p,p_max,e_max,e_c,batt_deg,reward,c_w,t_ch_coefficient):
        self.pev_num = pev_num
        self.lam = lam
        self.s = s
        self.r = r
        self.soc_i_mu = soc_i_p["mu"]
        self.soc_i_sigma = soc_i_p["sigma"]
        self.p_max = p_max
        self.e_max = e_max
        self.e_c = e_c
        self.batt_deg = batt_deg
        self.reward = reward
        self.c_w = c_w
        self.t_ch_coefficient = t_ch_coefficient
        self.soc_rs=soc_rs
        self.pevs = dict()
        for soc_r in self.soc_rs:
            self.env = Environment()
            self.temp_pevs = list()
            self.soc_r = soc_r
            self.stop_event = Event(self.env)
            self.env.process(self.run_charging_station())
            self.env.run(self.stop_event)
            self.temp_pevs = pd.DataFrame(self.temp_pevs)
            self.temp_pevs.set_index("pev", inplace = True)
            self.pevs[soc_r] = self.temp_pevs

    # process function for the simulation to run until a specified number of PEVs is charged
    def run_charging_station(self):
        charging_station = ChargingStation(self.env, self.s, self.r)
        i = 0
        while True:
            # wait time until next PEV has to be introduced to the simulation
            yield self.env.timeout(random.expovariate(self.lam/60))
            i += 1
            if charging_station.admission:
                # create a new PEV in the simulation and send it to the charging station
                pev = Pev(self.soc_r, i, self)
                self.env.process(pev.go_to_charging_station(self.env,charging_station))
            if i >= self.pev_num:
                charging_station.admission = False
    
    def get_mean_charging_time(self):
        temp1 = dict()
        for soc_r in self.soc_rs:
            temp2 = self.pevs[soc_r][self.pevs[soc_r]["blocked"]==False]
            temp1[soc_r] = (temp2["departure_time"]-temp2["start_time"]).mean()
        return temp1
    
    def get_mean_charging_power(self, numerical=False):
        temp1 = dict()
        if numerical:
            t_ch = self.get_mean_charging_time()
            for soc_r in self.soc_rs:
                temp2 = self.pevs[soc_r][self.pevs[soc_r]["blocked"]==False]
                temp1[soc_r] = 60.0*self.e_max*(soc_r - temp2["soc_i"].mean())/t_ch[soc_r]
        else:
            for soc_r in self.soc_rs:
                temp2 = self.pevs[soc_r][self.pevs[soc_r]["blocked"]==False]
                temp1[soc_r] = temp2["mean_power"].mean()
        return temp1
    
    def get_traffic_intensity(self):
        temp = dict()
        mu_over_1 = self.get_mean_charging_time()
        for soc_r in self.soc_rs:
            temp[soc_r] = mu_over_1[soc_r]*self.lam/(60*self.s)
        return temp
    
    def get_blocking_probability(self, numerical=False):
        temp1 = dict()
        if numerical:
            ro = self.get_traffic_intensity()
            theta = (self.s-1.0)/(self.s+1.0)
            f = (sqrt((9.0+theta)/(1.0-theta))-2)*theta/(8.0+8.0*theta)
            for soc_r in self.soc_rs:
                temp2 = self.pevs[soc_r][self.pevs[soc_r]["blocked"]==False]
                c_s = (temp2["departure_time"]-temp2["arrival_time"]).std()/60.0
                g = (1.0-ro[soc_r])/ro[soc_r]
                r_d = (1.0+f*g*(1-exp(-theta/(f*g))))/2.0
                r_g = ((1.0+c_s**2.0)*r_d)/((2.0*r_d-1.0)*c_s**2.0+1.0)
                zeta = ro[soc_r]*r_g/(1.0-ro[soc_r])+ro[soc_r]*r_g
                p_0 = 1.0/sum([((self.s*ro[soc_r])**j)/factorial(j)+(((self.s*ro[soc_r])**self.s)/factorial(self.s))*((1.0-ro[soc_r]*zeta**self.r)/(1.0-ro[soc_r])) for j in range(self.s)])
                temp1[soc_r] = ((self.s*ro[soc_r])**self.s)*(zeta**self.r)*p_0/factorial(self.s)
        else:
            for soc_r in self.soc_rs:
                temp1[soc_r] = len(self.pevs[soc_r][self.pevs[soc_r]["blocked"]==True].index)/len(self.pevs[soc_r].index)
        return temp1
    
    def get_mean_waiting_time(self, numerical=False):
        temp1 = dict()
        if numerical:
            ro = self.get_traffic_intensity()
            theta = (self.s-1.0)/(self.s+1.0)
            f = (sqrt((9.0+theta)/(1.0-theta))-2)*theta/(8.0+8.0*theta)
            for soc_r in self.soc_rs:
                temp2 = self.pevs[soc_r][self.pevs[soc_r]["blocked"]==False]
                c_s = (temp2["departure_time"]-temp2["arrival_time"]).std()/60.0
                g = (1.0-ro[soc_r])/ro[soc_r]
                r_d = (1.0+f*g*(1-exp(-theta/(f*g))))/2.0
                r_g = ((1.0+c_s**2.0)*r_d)/((2.0*r_d-1.0)*c_s**2.0+1.0)
                zeta = ro[soc_r]*r_g/(1.0-ro[soc_r])+ro[soc_r]*r_g
                p_0 = 1.0/sum([((self.s*ro[soc_r])**j)/factorial(j)+(((self.s*ro[soc_r])**self.s)/factorial(self.s))*((1.0-ro[soc_r]*zeta**self.r)/(1.0-ro[soc_r])) for j in range(self.s)])
                temp1[soc_r] = 60.0*((self.s*ro[soc_r])**self.s)*zeta*(1.0-zeta**self.r-self.r*(1.0-zeta)*ro[soc_r]*zeta**(self.r-1.0))*p_0/(factorial(self.s)*(1.0-ro[soc_r])*(1.0-zeta)*self.lam)
        else:
            for soc_r in self.soc_rs:
                temp2 = self.pevs[soc_r][self.pevs[soc_r]["blocked"]==False]
                temp1[soc_r] = (temp2["start_time"]-temp2["arrival_time"]).mean()
        return temp1
    
    def get_system_revenue(self):
        #TODO add calculation results too
        temp1 = dict()
        reward = lambda x: self.reward["m"]*x+self.reward["n"]
        p_k = self.get_blocking_probability()
        mean_t_w = self.get_mean_waiting_time()
        mean_t_ch = self.get_mean_charging_time()
        for soc_r in self.soc_rs:
            temp2 = self.pevs[soc_r][self.pevs[soc_r]["blocked"]==False]
            mean_c_batt = temp2["c_batt"].mean()
            temp1[soc_r] = self.lam*(1-p_k[soc_r])*(reward(soc_r)-self.c_w*mean_t_w[soc_r]/60.0-mean_c_batt*mean_t_ch[soc_r]/60.0)
        return temp1

    def get_results(self):
        return self.pevs

if __name__ == "__main__":
    sim = Simulation(
        pev_num=PEV_NUM,
        lam=LAM,
        s=S,
        r=R,
        soc_rs=SOC_RS,
        soc_i_p=SOC_I_P,
        p_max=P_MAX,
        e_max=E_MAX,
        e_c=E_C,
        batt_deg=BATT_DEG,
        reward=REWARD,
        c_w=C_W,
        t_ch_coefficient=T_CH_COEFFICIENT
    )
    print(sim.get_mean_charging_time())
    print(sim.get_mean_charging_power())
    print(sim.get_traffic_intensity())
    print(sim.get_blocking_probability())
    print(sim.get_mean_waiting_time())
    print(sim.get_system_revenue())