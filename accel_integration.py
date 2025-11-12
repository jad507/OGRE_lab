import pandas as pd
import numpy as np
from scipy.integrate import simpson, cumulative_simpson, solve_ivp
from scipy.interpolate import interp1d
import pathlib
import matplotlib
import matplotlib.pyplot as plt

# Load data
source_folder = pathlib.Path(r"D:\Reverse Telescope Test\accel\Session_2025-10-29_163326")
df = pd.read_csv(pathlib.Path.joinpath(source_folder, "AccelData_2025-10-29_163326_File0001.csv"))
t = df['RelativeTime_s'].values
ax = df['Mirror_X_g'].values * 9.80665
# ay = df['Mirror_Y_g'].values * 9.80665
# az = df['Mirror_Z_g'].values * 9.80665

# Integration using Simpson’s Rule
# Velocity from acceleration
vx = cumulative_simpson(y=ax, x=t, initial=0)
# vx = [simpson(ax[:i+1], t[:i+1]) for i in range(len(t))]
# vy = [simpson(ay[:i+1], t[:i+1]) for i in range(len(t))]
# vz = [simpson(az[:i+1], t[:i+1]) for i in range(len(t))]

# Position from velocity
px = cumulative_simpson(y=vx, x=t, initial=0)
# px = [simpson(vx[:i+1], t[:i+1]) for i in range(len(t))]
# py = [simpson(vy[:i+1], t[:i+1]) for i in range(len(t))]
# pz = [simpson(vz[:i+1], t[:i+1]) for i in range(len(t))]


plt.figure(figsize=(10,6))
plt.plot(t, ax, label='Acceleration (m/s²)')
plt.plot(t, vx, label='Velocity (m/s)')
# plt.plot(t, px, label='Displacement (m)')
plt.legend()
plt.xlabel('Time (s)')
plt.ylabel('Value')
plt.title('Acceleration → Velocity → Displacement')
plt.show()


# Integration using Runge-Kutta (solve_ivp)
# Interpolation for acceleration
ax_fun = interp1d(t, ax, kind='linear', fill_value='extrapolate')

def odefun_x(tt, y):
    return [ax_fun(tt), y[0]]  # [dv/dt, dx/dt]

y0 = [0, 0]
sol_x = solve_ivp(odefun_x, [t[0], t[-1]], y0, t_eval=t, method='RK45')
velocity_x = sol_x.y[0]
position_x = sol_x.y[1]
