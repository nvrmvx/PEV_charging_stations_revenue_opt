from math import log
import pandas as pd
import random

from simpy import Environment
from simpy.rt import RealtimeEnvironment
from simpy import Resource
from simpy.events import Event

SOC_I_MU = 0.3
SOC_I_SIGMA = 0.15
P1_MAX = 45
P2_MAX = 22
E1_C = 4
E2_C = 5

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
        self.sim.temp_pevs.append(
            {
                "pev": i,
                "soc_i": soc_i,
                "charger": 0,
                "arrival_time": None,
                "start_time": None,
                "departure_time": None,
                "mean_power": None,
                "blocked": False
            }
        )

if __name__ == "__main__":
    #? env = RealtimeEnvironment(factor=0.1,strict=False)
    sim = Simulation(
        pev_num=500,
        lam=8,
        s=10,
        r1=3,
        r2=3,
        soc_rs=[0.60, 0.65, 0.70, 0.75, 0.80,0.85,0.90,0.95,0.99]
    )

def multiclass_dedicated():
    pass
# smth