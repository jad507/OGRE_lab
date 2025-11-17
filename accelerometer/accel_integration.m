%%% This is a script that will numerically integrate the accelerometer data that Nate has produced.
%%% Keep in mind that accelerometer data looks like this:
%%% AbsoluteTime,RelativeTime_s,Mirror_Y_g,Mirror_X_g,Mirror_Z_g,Desk_Y_g
%%% 2025-10-29 16:33:27.200,0.000000,-0.001054,-0.005731,-0.003451,-0.002179
%%% Code was produced primarily by Microsoft Copilot/Chat GPT-5

% Load data
source_folder = 'D:\Reverse Telescope Test\accel\Session_2025-10-29_163326';
data = readtable(fullfile(source_folder, 'AccelData_2025-10-29_163326_File0001.csv'));

% Extract time and acceleration (convert g to m/s^2)
t = data.RelativeTime_s;
ax = data.Mirror_X_g * 9.80665;
ay = data.Mirror_Y_g * 9.80665;
az = data.Mirror_Z_g * 9.80665;

%%Simpson's Rule

% Interpolate acceleration for continuous function
ax_fun = @(tt) interp1(t, ax, tt, 'linear');
ay_fun = @(tt) interp1(t, ay, tt, 'linear');
az_fun = @(tt) interp1(t, az, tt, 'linear');

% Velocity from acceleration
vx = arrayfun(@(tt) integral(ax_fun, t(1), tt), t);
%vy = arrayfun(@(tt) integral(ay_fun, t(1), tt, 'Method', 'Simpson'), t);
%vz = arrayfun(@(tt) integral(az_fun, t(1), tt, 'Method', 'Simpson'), t);

% Position from velocity
px = arrayfun(@(tt) integral(@(tau) interp1(t, vx, tau, 'linear'), t(1), tt), t);
%py = arrayfun(@(tt) integral(@(tau) interp1(t, vy, tau, 'linear'), t(1), tt, 'Method', 'Simpson'), t);
%pz = arrayfun(@(tt) integral(@(tau) interp1(t, vz, tau, 'linear'), t(1), tt, 'Method', 'Simpson'), t);

plot(t,px)

%%Runge-Kutta with ODE45

% Define ODE system: y(1)=velocity, y(2)=position
ax_fun = @(tt) interp1(t, ax, tt, 'linear');
odefun_x = @(tt, y) [ax_fun(tt); y(1)];

% Initial conditions
y0 = [0; 0];

% Solve
[t_sol, y_sol_x] = ode45(odefun_x, [t(1) t(end)], y0);
% y_sol_x(:,1) = velocity, y_sol_x(:,2) = position


