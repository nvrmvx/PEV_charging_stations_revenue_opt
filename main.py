from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import tkinter as tk

import single_class
import multiclass_dedicated
import multiclass_shared

MODEL_NAMES = [
    "Single Class Model",
    "Multi-Class Dedicated Model",
    "Multi-Class Shared Model"
]
XLABEL = "Requested SoC (%)"

def validate_value(val: str):
    try:
        float(val)
        return True
    except ValueError:
        return val == ""

def validate_value_with_commas(val: str):
    els = val.split(",")
    for el in els:
        try:
            float(el)
        except ValueError:
            return el == ""
    return True

class SingleClassWindow:
    def __init__(self,root_window: "RootWindow"):
        self.sim = None
        self.a1 = None
        self.a2 = None
        self.a3 = None
        self.a4 = None
        self.a5 = None
        self.a6 = None
        self.data_plot = None
        self.root_window = root_window
        self.window = tk.Toplevel(self.root_window.root)
        self.window.title("Single Class Model Simulation Configuration")
        self.window.resizable(width=False,height=False)
        self.window.config(bg="#fff")
        self.window.grid()
        self.pev_num_val = tk.IntVar(self.window)
        self.pev_num_val.set(single_class.PEV_NUM)
        self.lam_val = tk.DoubleVar(self.window)
        self.lam_val.set(single_class.LAM)
        self.s_val = tk.IntVar(self.window)
        self.s_val.set(single_class.S)
        self.r_val = tk.IntVar(self.window)
        self.r_val.set(single_class.R)
        self.soc_rs_val = tk.StringVar(self.window)
        self.soc_rs_val.set(str(single_class.SOC_RS)[1:-1].replace(" ",""))
        self.soc_i_mu_val = tk.DoubleVar(self.window)
        self.soc_i_mu_val.set(single_class.SOC_I_P["mu"])
        self.soc_i_sigma_val = tk.DoubleVar(self.window)
        self.soc_i_sigma_val.set(single_class.SOC_I_P["sigma"])
        self.p_max_val = tk.DoubleVar(self.window)
        self.p_max_val.set(single_class.P_MAX)
        self.e_max_val = tk.DoubleVar(self.window)
        self.e_max_val.set(single_class.E_MAX)
        self.e_c_val = tk.DoubleVar(self.window)
        self.e_c_val.set(single_class.E_C)
        self.t_ch_coefficient_val = tk.DoubleVar(self.window)
        self.t_ch_coefficient_val.set(single_class.T_CH_COEFFICIENT)
        self.batt_deg_a_val = tk.DoubleVar(self.window)
        self.batt_deg_a_val.set(single_class.BATT_DEG["a"])
        self.batt_deg_b_val = tk.DoubleVar(self.window)
        self.batt_deg_b_val.set(single_class.BATT_DEG["b"])
        self.batt_deg_c_val = tk.DoubleVar(self.window)
        self.batt_deg_c_val.set(single_class.BATT_DEG["c"])
        self.reward_m_val = tk.DoubleVar(self.window)
        self.reward_m_val.set(single_class.REWARD["m"])
        self.reward_n_val = tk.DoubleVar(self.window)
        self.reward_n_val.set(single_class.REWARD["n"])
        self.c_w_val = tk.DoubleVar(self.window)
        self.c_w_val.set(single_class.C_W)
        self.soc_r_vis_val = tk.StringVar(self.window)
        self.time_vis_val = tk.DoubleVar(self.window)

        self.vcmd = (self.window.register(validate_value))
        self.vcmd2 = (self.window.register(validate_value_with_commas))
        pev_num_label = tk.Label(self.window,text="PEV number",background="#fff")
        pev_num_label.grid(column=0,row=0,padx=10,pady=5)
        pev_num = tk.Entry(self.window,textvariable=self.pev_num_val,validate="all",validatecommand=(self.vcmd, "%P"),width=7,background="#fff")
        pev_num.grid(column=1,row=0,padx=10,pady=5)
        lam_label = tk.Label(self.window,text="Lambda",background="#fff")
        lam_label.grid(column=0,row=1,padx=10,pady=5)
        lam = tk.Entry(self.window,textvariable=self.lam_val,validate="all",validatecommand=(self.vcmd, "%P"),width=7,background="#fff")
        lam.grid(column=1,row=1,padx=10,pady=5)
        s_label = tk.Label(self.window,text="Charger number",background="#fff")
        s_label.grid(column=0,row=2,padx=10,pady=5)
        s = tk.Entry(self.window,textvariable=self.s_val,validate="all",validatecommand=(self.vcmd, "%P"),width=7,background="#fff")
        s.grid(column=1,row=2,padx=10,pady=5)
        r_label = tk.Label(self.window,text="Waiting space number",background="#fff")
        r_label.grid(column=0,row=3,padx=10,pady=5)
        r = tk.Entry(self.window,textvariable=self.r_val,validate="all",validatecommand=(self.vcmd, "%P"),width=7,background="#fff")
        r.grid(column=1,row=3,padx=10,pady=5)
        self.soc_rs_label = tk.Label(self.window,text="SoC r (separated by commas)",background="#fff")
        self.soc_rs_label.grid(column=0,row=4,padx=10,pady=5)
        self.soc_rs = tk.Entry(self.window,textvariable=self.soc_rs_val,validate="all",validatecommand=(self.vcmd2, "%P"),width=7,background="#999")
        self.soc_rs.grid(column=1,row=4,padx=10,pady=5)
        soc_i_mu_label = tk.Label(self.window,text="SoC i mu",background="#fff")
        soc_i_mu_label.grid(column=2,row=0,padx=10,pady=5)
        soc_i_mu = tk.Entry(self.window,textvariable=self.soc_i_mu_val,validate="all",validatecommand=(self.vcmd, "%P"),width=7,background="#999")
        soc_i_mu.grid(column=3,row=0,padx=10,pady=5)
        soc_i_sigma_label = tk.Label(self.window,text="SoC i sigma",background="#fff")
        soc_i_sigma_label.grid(column=2,row=1,padx=10,pady=5)
        soc_i_sigma = tk.Entry(self.window,textvariable=self.soc_i_sigma_val,validate="all",validatecommand=(self.vcmd, "%P"),width=7,background="#999")
        soc_i_sigma.grid(column=3,row=1,padx=10,pady=5)
        p_max_label = tk.Label(self.window,text="P max",background="#fff")
        p_max_label.grid(column=2,row=2,padx=10,pady=5)
        p_max = tk.Entry(self.window,textvariable=self.p_max_val,validate="all",validatecommand=(self.vcmd, "%P"),width=7,background="#999")
        p_max.grid(column=3,row=2,padx=10,pady=5)
        e_max_label = tk.Label(self.window,text="E max",background="#fff")
        e_max_label.grid(column=2,row=3,padx=10,pady=5)
        e_max = tk.Entry(self.window,textvariable=self.e_max_val,validate="all",validatecommand=(self.vcmd, "%P"),width=7,background="#999")
        e_max.grid(column=3,row=3,padx=10,pady=5)
        e_c_label = tk.Label(self.window,text="E c",background="#fff")
        e_c_label.grid(column=2,row=4,padx=10,pady=5)
        e_c = tk.Entry(self.window,textvariable=self.e_c_val,validate="all",validatecommand=(self.vcmd, "%P"),width=7,background="#999")
        e_c.grid(column=3,row=4,padx=10,pady=5)
        t_ch_coefficient_label = tk.Label(self.window,text="Charging time coefficient",background="#fff")
        t_ch_coefficient_label.grid(column=2,row=5,padx=10,pady=5)
        t_ch_coefficient = tk.Entry(self.window,textvariable=self.t_ch_coefficient_val,validate="all",validatecommand=(self.vcmd, "%P"),width=7,background="#999")
        t_ch_coefficient.grid(column=3,row=5,padx=10,pady=5)
        batt_deg_a_label = tk.Label(self.window,text="Battery degradation a",background="#fff")
        batt_deg_a_label.grid(column=4,row=0,padx=10,pady=5)
        batt_deg_a = tk.Entry(self.window,textvariable=self.batt_deg_a_val,validate="all",validatecommand=(self.vcmd, "%P"),width=7,background="#999")
        batt_deg_a.grid(column=5,row=0,padx=10,pady=5)
        batt_deg_b_label = tk.Label(self.window,text="Battery degradation b",background="#fff")
        batt_deg_b_label.grid(column=4,row=1,padx=10,pady=5)
        batt_deg_b = tk.Entry(self.window,textvariable=self.batt_deg_b_val,validate="all",validatecommand=(self.vcmd, "%P"),width=7,background="#999")
        batt_deg_b.grid(column=5,row=1,padx=10,pady=5)
        batt_deg_c_label = tk.Label(self.window,text="Battery degradation c",background="#fff")
        batt_deg_c_label.grid(column=4,row=2,padx=10,pady=5)
        batt_deg_c = tk.Entry(self.window,textvariable=self.batt_deg_c_val,validate="all",validatecommand=(self.vcmd, "%P"),width=7,background="#999")
        batt_deg_c.grid(column=5,row=2,padx=10,pady=5)
        reward_m_label = tk.Label(self.window,text="Reward m",background="#fff")
        reward_m_label.grid(column=4,row=3,padx=10,pady=5)
        reward_m = tk.Entry(self.window,textvariable=self.reward_m_val,validate="all",validatecommand=(self.vcmd, "%P"),width=7,background="#999")
        reward_m.grid(column=5,row=3,padx=10,pady=5)
        reward_n_label = tk.Label(self.window,text="Reward n",background="#fff")
        reward_n_label.grid(column=4,row=4,padx=10,pady=5)
        reward_n = tk.Entry(self.window,textvariable=self.reward_n_val,validate="all",validatecommand=(self.vcmd, "%P"),width=7,background="#999")
        reward_n.grid(column=5,row=4,padx=10,pady=5)
        c_w_label = tk.Label(self.window,text="Waiting cost",background="#fff")
        c_w_label.grid(column=4,row=5,padx=10,pady=5)
        c_w = tk.Entry(self.window,textvariable=self.c_w_val,validate="all",validatecommand=(self.vcmd, "%P"),width=7,background="#999")
        c_w.grid(column=5,row=5,padx=10,pady=5)
        sim_button = tk.Button(self.window, text="Simulate", command=self.open_result_window)
        sim_button.grid(column=1,row=5,padx=10,pady=5)
    
    def open_result_window(self):
        #TODO do validity checks for empty parameters
        if self.root_window.model_result_window:
            self.root_window.model_result_window.destroy()
            self.root_window.model_result_window = None
        self.root_window.model_result_window = tk.Toplevel(self.window)
        self.root_window.model_result_window.config(bg="#fff")
        self.root_window.model_result_window.grid()
        buttons_frm = tk.Frame(self.root_window.model_result_window, bg="#fff")
        sim_button = tk.Button(buttons_frm, text="Re-Simulate", command=self.simulate)
        sim_button.grid(column=0,row=0,padx=(0,120),pady=(60,5))
        soc_r_vis_label = tk.Label(buttons_frm,text="SoC r to visualize",background="#fff")
        soc_r_vis_label.grid(column=1,row=0,padx=10,pady=(60,5))
        self.soc_r_vis = tk.OptionMenu(buttons_frm,self.soc_r_vis_val,"")
        self.soc_r_vis.grid(column=2,row=0,padx=10,pady=(60,5))
        time_vis_label = tk.Label(buttons_frm,text="Visualization time (minutes)",background="#fff")
        time_vis_label.grid(column=1,row=1,padx=10,pady=5)
        self.time_vis_val.set(30.0)
        time_vis = tk.Entry(buttons_frm,textvariable=self.time_vis_val,validate="all",validatecommand=(self.vcmd, "%P"),width=10)
        time_vis.grid(column=2,row=1,padx=10,pady=5)
        vis_button = tk.Button(buttons_frm, text="Visualize", command=self.open_visual_window)
        vis_button.grid(column=3,row=0,padx=10,pady=(60,5))
        buttons_frm.grid()
        fig = plt.Figure(figsize=(2, 3), dpi=72)
        self.a1 = fig.add_subplot(231)
        self.a2 = fig.add_subplot(232)
        self.a3 = fig.add_subplot(233)
        self.a4 = fig.add_subplot(234)
        self.a5 = fig.add_subplot(235)
        self.a6 = fig.add_subplot(236)
        self.data_plot = FigureCanvasTkAgg(fig, master=self.root_window.model_result_window)
        self.data_plot.get_tk_widget().config(height=550,width=1100)
        self.data_plot.get_tk_widget().grid()
        self.simulate()
    
    def simulate(self):
        self.sim = single_class.Simulation(
            pev_num=int(self.pev_num_val.get()),
            lam=self.lam_val.get(),
            s=int(self.s_val.get()),
            r=int(self.r_val.get()),
            soc_rs=sorted([float(num) for num in self.soc_rs_val.get().split(",") if num != ""]),
            soc_i_p={"mu": self.soc_i_mu_val.get(),"sigma": self.soc_i_sigma_val.get()},
            p_max=self.p_max_val.get(),
            e_max=self.e_max_val.get(),
            e_c=self.e_c_val.get(),
            batt_deg={"a": self.batt_deg_a_val.get(),"b": self.batt_deg_b_val.get(),"c": self.batt_deg_c_val.get()},
            reward={"m": self.reward_m_val.get(),"n": self.reward_n_val.get()},
            c_w=self.c_w_val.get(),
            t_ch_coefficient=self.t_ch_coefficient_val.get()
        )
        self.soc_r_vis_val.set("")
        self.soc_r_vis["menu"].delete(0, "end")
        soc_rs = [str(soc_r) for soc_r in self.sim.soc_rs]
        for soc_r in soc_rs:
            self.soc_r_vis["menu"].add_command(label=soc_r, command=tk._setit(self.soc_r_vis_val, soc_r))
        self.soc_r_vis_val.set(soc_rs[0])
        a1_dict = self.sim.get_mean_charging_time()
        self.a1.cla()
        self.a1.set_xlabel(XLABEL)
        self.a1.set_ylabel("Mean charging time (minutes)")
        self.a1.plot(list(a1_dict.keys()),list(a1_dict.values()))
        self.a1.set_xticks(self.sim.soc_rs)
        self.a1.set_ylim(0,None)
        self.a1.set_xlim(None,self.sim.soc_rs[-1])
        a2_dict = self.sim.get_mean_charging_power()
        self.a2.cla()
        self.a2.set_xlabel(XLABEL)
        self.a2.set_ylabel("Mean charging power (kWh)")
        self.a2.plot(list(a2_dict.keys()),list(a2_dict.values()))
        self.a2.set_xticks(self.sim.soc_rs)
        self.a2.set_ylim(0,None)
        self.a2.set_xlim(None,self.sim.soc_rs[-1])
        a3_dict = self.sim.get_traffic_intensity()
        self.a3.cla()
        self.a3.set_xlabel(XLABEL)
        self.a3.set_ylabel("Traffic intensity (cars per minute)")
        self.a3.plot(list(a3_dict.keys()),list(a3_dict.values()))
        self.a3.set_xticks(self.sim.soc_rs)
        self.a3.set_ylim(0,None)
        self.a3.set_xlim(None,self.sim.soc_rs[-1])
        a4_dict = self.sim.get_blocking_probability()
        self.a4.cla()
        self.a4.set_xlabel(XLABEL)
        self.a4.set_ylabel("Blocking probability (%)")
        self.a4.plot(list(a4_dict.keys()),list(a4_dict.values()))
        self.a4.set_xticks(self.sim.soc_rs)
        self.a4.set_ylim(0,None)
        self.a4.set_xlim(None,self.sim.soc_rs[-1])
        a5_dict = self.sim.get_mean_waiting_time()
        self.a5.cla()
        self.a5.set_xlabel(XLABEL)
        self.a5.set_ylabel("Mean waiting time (minutes)")
        self.a5.plot(list(a5_dict.keys()),list(a5_dict.values()))
        self.a5.set_xticks(self.sim.soc_rs)
        self.a5.set_ylim(0,None)
        self.a5.set_xlim(None,self.sim.soc_rs[-1])
        a6_dict = self.sim.get_system_revenue()
        self.a6.cla()
        self.a6.set_xlabel(XLABEL)
        self.a6.set_ylabel("System revenue ($ per hour)")
        self.a6.plot(list(a6_dict.keys()),list(a6_dict.values()))
        self.a6.set_xticks(self.sim.soc_rs)
        self.a6.set_ylim(0,None)
        self.a6.set_xlim(None,self.sim.soc_rs[-1])
        self.data_plot.draw()
    
    #TODO finish the visualization logic
    def open_visual_window(self):
        if self.root_window.model_visual_window:
            self.root_window.model_visual_window.destroy()
            self.root_window.model_visual_window = None
        self.root_window.model_visual_window = tk.Toplevel(self.root_window.model_result_window)
        self.root_window.model_visual_window.config(bg="#fff")
        self.root_window.model_visual_window.grid()

class RootWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PEV Charging Station Simulation Configuration")
        self.root.geometry("450x110")
        self.root.resizable(width=False,height=False)
        self.root.config(bg="#fff")
        self.frm = tk.Frame(self.root,pady=10,bg="#fff")
        self.model_config_window = None
        self.model_result_window = None
        self.model_visual_window = None
        self.root.option_add("*Font", "Times 12")
        self.model_type_val = tk.StringVar(self.frm)
        self.model_type_val.set(MODEL_NAMES[0])
        self.frm.grid()
        self.frm.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.type_opt_label = tk.Label(self.frm,text="Type:",background="#fff")
        self.type_opt_label.grid(column=0,row=0,pady=5)
        self.type_opt = tk.OptionMenu(self.frm,self.model_type_val,*MODEL_NAMES)
        self.type_opt.grid(column=1,row=0,pady=5)
        self.type_button = tk.Button(self.frm,text="Choose",command=self.choose_model)
        self.type_button.grid(column=0,row=1,pady=5,columnspan=2)
        self.root.mainloop()

    def choose_model(self):
        if self.model_config_window:
            self.model_config_window.window.destroy()
            self.model_config_window = None
        if self.model_type_val.get() == MODEL_NAMES[0]:
            self.model_config_window = SingleClassWindow(self)
        if self.model_type_val.get() == MODEL_NAMES[1]:
            print(f"{MODEL_NAMES[1]} window is supposed to show up here")
        if self.model_type_val.get() == MODEL_NAMES[2]:
            print(f"{MODEL_NAMES[2]} window is supposed to show up here")

if __name__ == "__main__":
    RootWindow()