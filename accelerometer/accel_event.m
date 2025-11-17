function accel_event()

clc; clear; close all;

CONFIG = struct();
CONFIG.channels = [17, 18, 19, 20];
CONFIG.channel_names = {'Mirror_Y', 'Mirror_X', 'Mirror_Z', 'Desk_Y'};
CONFIG.sample_rate = 10000;  % SAMPLE RATE
CONFIG.hardware_gain = 100;  % CURRENT GAIN SETTING ON SIGNAL CONDITIONER (REQUIRES DISASSEMBLY TO CHANGE)
CONFIG.sensitivity = 0.100;  % ACCELEROMETER UNIT CONVERSION: 0.100 V / g
CONFIG.log_directory = '';   % DATA FILES WILL BE SAVED HERE, ADD YOUR DESIRED DIRECTORY, Ex: 'C:\Users\Nate\OneDrive\Desktop\LAB Files\Accelerometer Data
CONFIG.threshold_magnitude = 0.05; % CUTOFF MAGNITUDE FOR SAVED EVENT POINTS
CONFIG.smoothing_factor = 0;       % EXPONTNTIAL SMOOTHING FACTOR: new_data_point = (last point)*(smoothing_factor) + (current point)*(1 - smoothing_factor)

fprintf('=== Reverse Telescope Accelerometer DAQ (Event-Based) ===\n');

if ~exist(CONFIG.log_directory, 'dir')
    mkdir(CONFIG.log_directory);
end

session_id = datestr(now, 'yyyy-mm-dd_HHMMSS');
session_dir = fullfile(CONFIG.log_directory, ['Session_', session_id]);
mkdir(session_dir);
fprintf('Session directory: %s\n\n', session_dir);

try
    dq = daq.createSession('ni');
    for i = 1:length(CONFIG.channels)
        addAnalogInputChannel(dq, 'Dev1', CONFIG.channels(i), 'Voltage');
        dq.Channels(i).Range = [-10, 10];
    end
    dq.Rate = CONFIG.sample_rate;
    dq.IsContinuous = true;
    dq.NotifyWhenDataAvailableExceeds = 200;
    fprintf('DAQ initialized\n');
catch ME
    error('DAQ failed: %s', ME.message);
end

global DATA_BUFFER SESSION_DATA LOGGER CONFIG_GLOBAL;

CONFIG_GLOBAL = CONFIG;

EVENT_BUFFER_SIZE = CONFIG.sample_rate * 2;
DATA_BUFFER = struct();
DATA_BUFFER.timestamps = zeros(EVENT_BUFFER_SIZE, 1);
DATA_BUFFER.accel_data = zeros(EVENT_BUFFER_SIZE, 4);
DATA_BUFFER.write_index = 1;
DATA_BUFFER.sample_count = 0;
DATA_BUFFER.smoothed = zeros(1, 4);
DATA_BUFFER.last_was_above_threshold = false;

SESSION_DATA = struct();
SESSION_DATA.start_time = now;
SESSION_DATA.start_tic = tic;
SESSION_DATA.stop_requested = false;
SESSION_DATA.session_dir = session_dir;
SESSION_DATA.session_id = session_id;
SESSION_DATA.events_collected = 0;
SESSION_DATA.samples_written = 0;

LOGGER = struct();
LOGGER.file_counter = 1;
LOGGER.current_file = '';
LOGGER.samples_in_file = 0;
LOGGER.total_samples = 0;
LOGGER.fid = -1;

fprintf('Event threshold: %.3f g\n\n', CONFIG.threshold_magnitude);

fig = figure('Name', 'Accelerometer DAQ', ...
    'Position', [100, 100, 400, 150], ...
    'Color', 'white', ...
    'NumberTitle', 'off');

SESSION_DATA.figure_handle = fig;
SESSION_DATA.duration_text = uicontrol('Style', 'text', 'Units', 'normalized', ...
    'Position', [0.05, 0.65, 0.9, 0.25], ...
    'String', 'Duration: 00:00:00', ...
    'FontSize', 14, 'FontWeight', 'bold', ...
    'BackgroundColor', [0.95, 0.95, 0.95]);

SESSION_DATA.events_text = uicontrol('Style', 'text', 'Units', 'normalized', ...
    'Position', [0.05, 0.35, 0.9, 0.25], ...
    'String', 'Events: 0', ...
    'FontSize', 14, 'FontWeight', 'bold', ...
    'BackgroundColor', [0.95, 0.95, 0.95]);

SESSION_DATA.files_text = uicontrol('Style', 'text', 'Units', 'normalized', ...
    'Position', [0.05, 0.05, 0.9, 0.25], ...
    'String', 'Files: 1', ...
    'FontSize', 14, 'FontWeight', 'bold', ...
    'BackgroundColor', [0.95, 0.95, 0.95]);

create_new_binary_file();

data_listener = addlistener(dq, 'DataAvailable', @data_callback_event);
SESSION_DATA.data_listener = data_listener;

display_timer = timer();
set(display_timer, 'ExecutionMode', 'fixedRate');
set(display_timer, 'Period', 0.5);
set(display_timer, 'TimerFcn', @display_callback_stats);
SESSION_DATA.display_timer = display_timer;

set(fig, 'KeyPressFcn', @keyboard_callback_event);
set(fig, 'CloseRequestFcn', @cleanup_callback_event);

fprintf('RUNNING (Press SPACE to flush, ESC to stop)\n\n');

try
    start(display_timer);
    startBackground(dq);
    
    while ishandle(fig) && ~SESSION_DATA.stop_requested
        pause(1);
    end
catch ME
    fprintf('System error: %s\n', ME.message);
end

cleanup_system_event();

end

function data_callback_event(~, event)

global DATA_BUFFER SESSION_DATA LOGGER CONFIG_GLOBAL;

try
    raw_data = event.Data;
    timestamps = event.TimeStamps;
    n_samples = size(raw_data, 1);
    
    for k = 1:n_samples
        raw_g = (raw_data(k, :) / CONFIG_GLOBAL.hardware_gain) / CONFIG_GLOBAL.sensitivity;
        
        DATA_BUFFER.smoothed = CONFIG_GLOBAL.smoothing_factor * DATA_BUFFER.smoothed + ...
            (1 - CONFIG_GLOBAL.smoothing_factor) * raw_g;
        
        idx = DATA_BUFFER.write_index;
        DATA_BUFFER.timestamps(idx) = timestamps(k);
        DATA_BUFFER.accel_data(idx, :) = DATA_BUFFER.smoothed;
        
        DATA_BUFFER.write_index = mod(DATA_BUFFER.write_index, length(DATA_BUFFER.timestamps)) + 1;
        DATA_BUFFER.sample_count = DATA_BUFFER.sample_count + 1;
        
        max_accel = max(abs(DATA_BUFFER.smoothed));
        is_above_threshold = max_accel >= CONFIG_GLOBAL.threshold_magnitude;
        
        if is_above_threshold
            log_sample_to_binary_event(timestamps(k), DATA_BUFFER.smoothed);
            SESSION_DATA.samples_written = SESSION_DATA.samples_written + 1;
            DATA_BUFFER.last_was_above_threshold = true;
        else
            if DATA_BUFFER.last_was_above_threshold
                SESSION_DATA.events_collected = SESSION_DATA.events_collected + 1;
                DATA_BUFFER.last_was_above_threshold = false;
            end
        end
    end
    
catch
end

end

function display_callback_stats(~, ~)

global SESSION_DATA LOGGER;

try
    if ~ishandle(SESSION_DATA.figure_handle)
        return;
    end
    
    elapsed_sec = toc(SESSION_DATA.start_tic);
    hours = floor(elapsed_sec / 3600);
    minutes = floor(mod(elapsed_sec, 3600) / 60);
    seconds = floor(mod(elapsed_sec, 60));
    
    duration_str = sprintf('Duration: %02d:%02d:%02d', hours, minutes, seconds);
    set(SESSION_DATA.duration_text, 'String', duration_str);
    
    events_str = sprintf('Events: %d', SESSION_DATA.events_collected);
    set(SESSION_DATA.events_text, 'String', events_str);
    
    files_str = sprintf('Files: %d', LOGGER.file_counter);
    set(SESSION_DATA.files_text, 'String', files_str);
    
    drawnow limitrate;
    
catch
end

end

function keyboard_callback_event(~, event)

global SESSION_DATA LOGGER;

switch event.Key
    case 'space'
        if LOGGER.fid ~= -1
            fflush(LOGGER.fid);
        end
        fprintf('[%s] Flushed\n', datestr(now, 'HH:MM:SS'));
        
    case 'escape'
        SESSION_DATA.stop_requested = true;
end

end

function cleanup_callback_event(~, ~)

global SESSION_DATA;

SESSION_DATA.stop_requested = true;
cleanup_system_event();

end

function log_sample_to_binary_event(timestamp, accel_data)

global LOGGER CONFIG_GLOBAL SESSION_DATA;

try
    MAX_SAMPLES_PER_FILE = 1000000;
    
    if LOGGER.samples_in_file >= MAX_SAMPLES_PER_FILE
        close_current_binary_file_event();
        create_new_binary_file();
    end
    
    if LOGGER.fid ~= -1
        sample_data = [timestamp, accel_data];
        count = fwrite(LOGGER.fid, sample_data, 'double');
        
        if count == 5
            LOGGER.samples_in_file = LOGGER.samples_in_file + 1;
            LOGGER.total_samples = LOGGER.total_samples + 1;
        end
    end
    
catch
end

end

function create_new_binary_file()

global LOGGER SESSION_DATA;

try
    filename = sprintf('EventData_%s_File%04d.bin', SESSION_DATA.session_id, LOGGER.file_counter);
    filepath = fullfile(SESSION_DATA.session_dir, filename);
    
    LOGGER.fid = fopen(filepath, 'wb');
    
    if LOGGER.fid ~= -1
        LOGGER.current_file = filepath;
        LOGGER.samples_in_file = 0;
        fprintf('[%s] File %d created\n', datestr(now, 'HH:MM:SS'), LOGGER.file_counter);
    end
    
catch ME
    fprintf('File creation error: %s\n', ME.message);
end

end

function close_current_binary_file_event()

global LOGGER SESSION_DATA;

try
    if LOGGER.fid ~= -1
        fclose(LOGGER.fid);
        LOGGER.fid = -1;
    end
    
    if LOGGER.samples_in_file > 0
        create_csv_companion_event();
    end
    
    LOGGER.file_counter = LOGGER.file_counter + 1;
    
catch
end

end

function create_csv_companion_event()

global LOGGER SESSION_DATA;

try
    bin_fid = fopen(LOGGER.current_file, 'rb');
    if bin_fid == -1, return; end
    
    data_matrix = fread(bin_fid, [5, LOGGER.samples_in_file], 'double');
    fclose(bin_fid);
    
    if isempty(data_matrix), return; end
    
    data_matrix = data_matrix';
    
    csv_filename = strrep(LOGGER.current_file, '.bin', '.csv');
    csv_fid = fopen(csv_filename, 'w');
    
    if csv_fid == -1, return; end
    
    fprintf(csv_fid, '%% EVENT-FILTERED DATA\n');
    fprintf(csv_fid, 'AbsoluteTime,RelativeTime_s,Mirror_Y_g,Mirror_X_g,Mirror_Z_g,Desk_Y_g\n');
    
    for i = 1:size(data_matrix, 1)
        abs_time = SESSION_DATA.start_time + data_matrix(i,1)/(24*3600);
        fprintf(csv_fid, '%s,%.6f,%.6f,%.6f,%.6f,%.6f\n', ...
            datestr(abs_time, 'yyyy-mm-dd HH:MM:SS.FFF'), ...
            data_matrix(i, 1), data_matrix(i, 2), data_matrix(i, 3), ...
            data_matrix(i, 4), data_matrix(i, 5));
    end
    
    fclose(csv_fid);
    
catch
end

end

function cleanup_system_event()

global SESSION_DATA DATA_BUFFER LOGGER CONFIG_GLOBAL;

fprintf('\n=== SHUTDOWN ===\n');

try
    if isfield(SESSION_DATA, 'display_timer') && isvalid(SESSION_DATA.display_timer)
        stop(SESSION_DATA.display_timer);
        delete(SESSION_DATA.display_timer);
    end
    
    close_current_binary_file_event();
    
    runtime_hours = (now - SESSION_DATA.start_time) * 24;
    
    fprintf('Runtime: %.2f hours\n', runtime_hours);
    fprintf('Events: %d\n', SESSION_DATA.events_collected);
    fprintf('Samples saved: %d\n', SESSION_DATA.samples_written);
    fprintf('Files: %d\n', LOGGER.file_counter);
    fprintf('Threshold: %.3f g\n', CONFIG_GLOBAL.threshold_magnitude);
    fprintf('Session: %s\n\n', SESSION_DATA.session_dir);
    
catch ME
    fprintf('Cleanup error: %s\n', ME.message);
end

if isfield(SESSION_DATA, 'figure_handle') && ishandle(SESSION_DATA.figure_handle)
    delete(SESSION_DATA.figure_handle);
end

end
