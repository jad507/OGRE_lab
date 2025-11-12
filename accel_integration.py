from typing import Optional, Any

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
ax = df['Mirror_X_g'].values * 386.1 # accel output from matlab is in g's. g = 386.1 inches/sec^2
ay = df['Mirror_Y_g'].values * 386.1
az = df['Mirror_Z_g'].values * 386.1
aarm = df['Desk_Y_g'].values * 386.1

def plotaccels(
        t: np.ndarray[Any, np.dtype[np.floating[Any]]],
        a: np.ndarray[Any, np.dtype[np.floating[Any]]],
        axis: str,
        suppressPosition: Optional = False) -> tuple[np.ndarray, Optional[np.ndarray]]:
    if len(t) != len(a):
        raise ValueError("All input arrays must have the same length.")
    v = cumulative_simpson(y=a, x=t, initial=0)
    p = cumulative_simpson(y=v, x=t, initial=0)

    plt.figure(figsize=(10, 6))
    plt.plot(t, a, label=f'{axis} Acceleration (in/s²)')
    plt.plot(t, v, label=f'{axis} Velocity (in/s)')
    if not suppressPosition:
        plt.plot(t, p, label=f'{axis} Displacement (in)')
    plt.legend()
    plt.xlabel('Time (s)')
    plt.ylabel('Value')
    plt.title(f'{axis} Acceleration → Velocity → Displacement')
    plt.show()

    return v, p

vx, px = plotaccels(t, ax, "X")

# Integration using Runge-Kutta (solve_ivp)
# Interpolation for acceleration
ax_fun = interp1d(t, ax, kind='linear', fill_value='extrapolate')

def odefun_x(tt, y):
    return [ax_fun(tt), y[0]]  # [dv/dt, dx/dt]

y0 = [0, 0]
sol_x = solve_ivp(odefun_x, [t[0], t[-1]], y0, t_eval=t, method='RK45')
velocity_x = sol_x.y[0]
position_x = sol_x.y[1]
