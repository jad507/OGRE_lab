import pandas as pd
import numpy as np
from scipy.integrate import simps, solve_ivp
from scipy.interpolate import interp1d
import pathlib

# Load data
source_folder = pathlib.Path(r"D:\Reverse Telescope Test\accel\Session_2025-10-29_163326")
df = pd.read_csv(pathlib.join(source_folder, "AccelData_2025-10-29_163326_File0001.csv"))
t = df['RelativeTime_s'].values
ax = df['Mirror_X_g'].values * 9.80665
ay = df['Mirror_Y_g'].values * 9.80665
az = df['Mirror_Z_g'].values * 9.80665

# Integration using Simpson’s Rule
# Velocity from acceleration
vx = [simps(ax[:i+1], t[:i+1]) for i in range(len(t))]
vy = [simps(ay[:i+1], t[:i+1]) for i in range(len(t))]
vz = [simps(az[:i+1], t[:i+1]) for i in range(len(t))]

# Position from velocity
px = [simps(vx[:i+1], t[:i+1]) for i in range(len(t))]
py = [simps(vy[:i+1], t[:i+1]) for i in range(len(t))]
pz = [simps(vz[:i+1], t[:i+1]) for i in range(len(t))]


# Integration using Runge-Kutta (solve_ivp)
# Interpolation for acceleration
ax_fun = interp1d(t, ax, kind='linear', fill_value='extrapolate')

def odefun_x(tt, y):
    return [ax_fun(tt), y[0]]  # [dv/dt, dx/dt]

y0 = [0, 0]
sol_x = solve_ivp(odefun_x, [t[0], t[-1]], y0, t_eval=t, method='RK45')
velocity_x = sol_x.y[0]
position_x = sol_x.y[1]
