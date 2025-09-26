% accel_readout_with_smoothing.m
clc; clear; close all;

%% User settings
sampleRate      = input('Enter desired sample rate (Hz): ');
smoothingFactor = input('Enter smoothing factor (0–1, larger = smoother): ');
windowSec       = 5;   % seconds for frequency estimation

%% Initialize DAQ
s = daq("ni");
addinput(s, "dev1", 17:19, "Voltage");
s.Rate = sampleRate;

%% Data storage
timeVec      = [];
dataRaw      = [];     % Nx3 raw voltages
dataSmooth   = [];     % Nx3 smoothed voltages
smoothedPrev = zeros(1,3);

%% Set up figure and plots
fig = figure('Name','Accelerometer Readout','NumberTitle','off');
for i = 1:3
    ax(i) = subplot(3,1,i);
    lines(i) = animatedline('Color','b');
    ylabel(ax(i), sprintf('Ch%d (V)', 16+i));
    hold(ax(i), 'on');
    freqText(i) = text(0.1, 0.9, '', 'Units','normalized', ...
                       'FontSize',10, 'Color','r');
end
xlabel(ax(3), 'Time (s)');
linkaxes(ax, 'x');
startT = tic;
disp('Press Ctrl+C or close window to stop.');

%% Acquisition loop
try
    while isvalid(fig)
        % Read raw sample
        raw = read(s, 1, "OutputFormat", "Matrix");  % 1×3
        t   = toc(startT);
        
        % Exponential smoothing
        smoothedPrev = smoothingFactor * smoothedPrev ...
                     + (1 - smoothingFactor) * raw;
        smooth = smoothedPrev;
        
        % Store data
        timeVec(end+1,1)    = t;
        dataRaw(end+1, :)   = raw;
        dataSmooth(end+1, :)= smooth;
        
        % Update plots (smoothed)
        for i = 1:3
            addpoints(lines(i), t, smooth(i));
        end
        xlim(ax, max(0, t-10) + [0, 10]);
        drawnow limitrate;
        
        % Frequency estimation on smoothed data
        idx = find(timeVec >= t - windowSec);
        if numel(idx) > 10
            for i = 1:3
                ywin = dataSmooth(idx, i);
                twin = timeVec(idx);
                [~, locs] = findpeaks(ywin, twin, 'MinPeakProminence', 0.05);
                f_est = numel(locs) / (twin(end) - twin(1));
                freqText(i).String = sprintf('Freq ≈ %.2f Hz', f_est);
            end
        end
    end
catch ME
    if ~strcmp(ME.identifier, "MATLAB:class:InvalidHandle")
        rethrow(ME)
    end
end

%% Cleanup and save CSV
clear s
disp('Session closed.');

timestamp = datestr(now,'yyyymmdd_HHMMSS');
filename = sprintf('accelerometer_data_%s.csv', timestamp);
T = table(timeVec, dataRaw(:,1), dataRaw(:,2), dataRaw(:,3), ...
          dataSmooth(:,1), dataSmooth(:,2), dataSmooth(:,3), ...
          'VariableNames', {'Time_s','Ch17_Raw','Ch18_Raw','Ch19_Raw', ...
                            'Ch17_Smooth','Ch18_Smooth','Ch19_Smooth'});
writetable(T, filename);
fprintf('Data saved to %s\n', filename);
