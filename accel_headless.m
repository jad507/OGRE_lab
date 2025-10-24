
function accel_headless()
% Headless version of the accelerometer DAQ script

clc; clear;

%% CONFIGURATION
CONFIG = struct();
CONFIG.channels = [17, 18, 19, 20];
CONFIG.channel_names = {'Mirror_Y', 'Mirror_X', 'Mirror_Z', 'Desk_Y'};
CONFIG.sample_rate = 1000;
CONFIG.hardware_gain = 100;
CONFIG.sensitivity = 0.1;
CONFIG.log_directory = 'C:\Users\tater\OneDrive\Desktop\LAB Files\Accelerometer Data';
CONFIG.samples_per_file = 300000;

fprintf('=== Headless Accelerometer DAQ ===
');

if ~exist(CONFIG.log_directory, 'dir')
    mkdir(CONFIG.log_directory);
end

session_id = datestr(now, 'yyyy-mm-dd_HHMMSS');
session_dir = fullfile(CONFIG.log_directory, ['Session_', session_id]);
mkdir(session_dir);
fprintf('Session directory: %s
', session_dir);

%% DAQ SETUP
try
    dq = daq.createSession('ni');
    for i = 1:length(CONFIG.channels)
        addAnalogInputChannel(dq, 'Dev1', CONFIG.channels(i), 'Voltage');
        dq.Channels(i).Range = [-10, 10];
    end
    dq.Rate = CONFIG.sample_rate;
    dq.IsContinuous = true;
    dq.NotifyWhenDataAvailableExceeds = 200;
    fprintf('DAQ initialized successfully
');
catch ME
    error('DAQ failed: %s', ME.message);
end

%% GLOBAL STRUCTURES
global DATA_BUFFER SESSION_DATA LOGGER CONFIG_GLOBAL;
CONFIG_GLOBAL = CONFIG;
BUFFER_SIZE = CONFIG.sample_rate * 60 * 30;
DATA_BUFFER.timestamps = zeros(BUFFER_SIZE, 1);
DATA_BUFFER.accel_data = zeros(BUFFER_SIZE, 4);
DATA_BUFFER.write_index = 1;
DATA_BUFFER.sample_count = 0;
DATA_BUFFER.smoothed = zeros(1, 4);

SESSION_DATA.start_time = now;
SESSION_DATA.start_tic = tic;
SESSION_DATA.stop_requested = false;
SESSION_DATA.session_dir = session_dir;
SESSION_DATA.session_id = session_id;

LOGGER.file_counter = 1;
LOGGER.current_file = '';
LOGGER.samples_in_file = 0;
LOGGER.total_samples = 0;
LOGGER.fid = -1;

%% FILE INIT
create_new_binary_file();

%% CALLBACK
data_listener = addlistener(dq, 'DataAvailable', @data_callback_matlab);
SESSION_DATA.data_listener = data_listener;

%% START ACQUISITION
fprintf('
=== STARTING HEADLESS ACQUISITION ===
');
startBackground(dq);

% Run for fixed duration (e.g., 5 minutes)
duration_sec = 300;
start_time = tic;
while toc(start_time) < duration_sec && ~SESSION_DATA.stop_requested
    pause(1);
end

%% CLEANUP
cleanup_system_matlab();
end
