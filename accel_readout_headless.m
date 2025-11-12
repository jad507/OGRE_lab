
function accel_readout_headless()
    % Main function wrapper for MATLAB compliance
    
    clc; clear; close all;
    
    %% MATLAB-COMPLIANT CONFIGURATION
    CONFIG = struct();
    CONFIG.channels = [17, 18, 19, 20];
    CONFIG.channel_names = {'Mirror_Y', 'Mirror_X', 'Mirror_Z', 'Desk_Y'};
    CONFIG.sample_rate = 1000;
    CONFIG.hardware_gain = 100; % 100x gain from signal conditioner
    CONFIG.sensitivity = 0.1; %.1 V/G
    
    CONFIG.log_directory = 'C:\Users\jad507\OneDrive - The Pennsylvania State University\Pictures\Reverse Telescope Test\accel';
    CONFIG.samples_per_file = 300000;  % 5 minutes per file
    CONFIG.display_rate = 25;
    CONFIG.display_seconds = 10;       % Exactly 10 seconds display window
    CONFIG.decimation_factor = 20;
    CONFIG.smoothing_factor = 0.1;
    
    fprintf('=== Reverse Telescope Accelerometer DAQ ===\n');
    
    %% FILE SYSTEM SETUP
    if ~exist(CONFIG.log_directory, 'dir')
        mkdir(CONFIG.log_directory);
    end
    
    session_id = char(datetime('now', 'Format', 'yyyy-MM-dd_HHmmss'));
    session_dir = fullfile(CONFIG.log_directory, ['Session_', session_id]);
    mkdir(session_dir);
    fprintf('Session directory: %s\n', session_dir);
    
    %% MATLAB DAQ INITIALIZATION
    try
        dq = daq.createSession('ni');
        for i = 1:length(CONFIG.channels)
            addAnalogInputChannel(dq, 'Dev1', CONFIG.channels(i), 'Voltage');
            dq.Channels(i).Range = [-10, 10];
        end
        dq.Rate = CONFIG.sample_rate;
        dq.IsContinuous = true;
        dq.NotifyWhenDataAvailableExceeds = 200;
        fprintf('DAQ initialized successfully\n');
    catch ME
        error('DAQ failed: %s', ME.message);
    end
    
    %% GLOBAL DATA STRUCTURES (MATLAB style)
    % Use global variables for callback access (MATLAB best practice)
    global DATA_BUFFER DISPLAY_BUFFER SESSION_DATA LOGGER CONFIG_GLOBAL;
    
    CONFIG_GLOBAL = CONFIG;
    
    % Main data buffer (30 minutes)
    BUFFER_SIZE = CONFIG.sample_rate * 60 * 30;
    DATA_BUFFER = struct();
    DATA_BUFFER.timestamps = zeros(BUFFER_SIZE, 1);
    DATA_BUFFER.accel_data = zeros(BUFFER_SIZE, 4);
    DATA_BUFFER.write_index = 1;
    DATA_BUFFER.sample_count = 0;
    DATA_BUFFER.smoothed = zeros(1, 4);
    
    % Display buffer
    DISPLAY_SIZE = CONFIG.sample_rate * CONFIG.display_seconds;
    DISPLAY_BUFFER = struct();
    DISPLAY_BUFFER.time = zeros(DISPLAY_SIZE, 1);
    DISPLAY_BUFFER.data = zeros(DISPLAY_SIZE, 4);
    DISPLAY_BUFFER.write_index = 1;
    DISPLAY_BUFFER.sample_count = 0;
    DISPLAY_BUFFER.decimation_counter = 0;
    
    % Session tracking
    SESSION_DATA = struct();
    SESSION_DATA.start_time = now;
    SESSION_DATA.start_tic = tic;
    SESSION_DATA.last_status = now;
    SESSION_DATA.stop_requested = false;
    SESSION_DATA.session_dir = session_dir;
    SESSION_DATA.session_id = session_id;
    
    % Logger structure
    LOGGER = struct();
    LOGGER.file_counter = 1;
    LOGGER.current_file = '';
    LOGGER.samples_in_file = 0;
    LOGGER.total_samples = 0;
    LOGGER.fid = -1;  % File handle for binary writing
    
    fprintf('Pre-allocated %.0f MB for data buffers\n', (BUFFER_SIZE * 5 * 8) / 1e6);
    
    %% CLEAN MATLAB GRAPHICS SETUP

    
    % Initialize first binary file
    create_new_binary_file();
    
    %% DATA CALLBACK - MATLAB STYLE
    data_listener = addlistener(dq, 'DataAvailable', @data_callback_matlab);
    SESSION_DATA.data_listener = data_listener;
    
    %% DISPLAY TIMER - MATLAB COMPLIANT
    SESSION_DATA.display_timer = timer();
    set(SESSION_DATA.display_timer, 'ExecutionMode', 'fixedRate');
    set(SESSION_DATA.display_timer, 'Period', 1/CONFIG.display_rate);
    set(SESSION_DATA.display_timer, 'TimerFcn', @display_callback_time_fixed);  % UPDATED: Time-fixed display
    
    
    %% START SYSTEM
    fprintf('\n=== INITIALIZING ===\n');
    
    try
        start(SESSION_DATA.display_timer)
        startBackground(dq);
        
        fprintf('=== RUNNING ===\n');
        fprintf('Press SPACE for manual save, ESC to stop\n\n');

        
        % Main loop - MATLAB style
    while ~SESSION_DATA.stop_requested
            pause(1);
            
            % Update global SESSION_DATA to check stop condition
            global SESSION_DATA;
            if SESSION_DATA.stop_requested
                break;
            end
        end
        
    catch ME
        fprintf('System error: %s\n', ME.message);
    end
    
    %% CLEANUP
    cleanup_system_matlab();
    
end % End of main function

%% MATLAB CALLBACK FUNCTIONS (separate functions, not nested)

function data_callback_matlab(~, event)
    % MATLAB-compliant data processing callback
    global DATA_BUFFER SESSION_DATA LOGGER CONFIG_GLOBAL;
    
    try
        raw_data = event.Data;
        timestamps = event.TimeStamps;
        n_samples = size(raw_data, 1);
        
        for k = 1:n_samples
            % Convert to g-forces
            raw_g = (raw_data(k, :) / CONFIG_GLOBAL.hardware_gain) / CONFIG_GLOBAL.sensitivity;
            DATA_BUFFER.smoothed = CONFIG_GLOBAL.smoothing_factor * DATA_BUFFER.smoothed + ...
                (1 - CONFIG_GLOBAL.smoothing_factor) * raw_g;
            
            % Store in buffer
            idx = DATA_BUFFER.write_index;
            DATA_BUFFER.timestamps(idx) = timestamps(k);
            DATA_BUFFER.accel_data(idx, :) = DATA_BUFFER.smoothed;
            
            % Update pointers
            DATA_BUFFER.write_index = DATA_BUFFER.write_index + 1;
            if DATA_BUFFER.write_index > length(DATA_BUFFER.timestamps)
                DATA_BUFFER.write_index = 1;
            end
            DATA_BUFFER.sample_count = DATA_BUFFER.sample_count + 1;
            
            % Binary logging - MATLAB style
            log_sample_to_binary_matlab(timestamps(k), DATA_BUFFER.smoothed);
            
        end
    catch
        % Silent error handling
    end
end

function keyboard_callback_matlab(~, event)
    % MATLAB keyboard handling
    global SESSION_DATA LOGGER;
    
    switch event.Key
        case 'space'
            % Manual flush
            if LOGGER.fid ~= -1
                fflush(LOGGER.fid);  % MATLAB function to flush file
            end
            fprintf('Manual flush completed\n');
            
        case 'escape'
            % Stop system
            SESSION_DATA.stop_requested = true;
    end
end

function cleanup_callback_matlab(~, ~)
    global SESSION_DATA;
    SESSION_DATA.stop_requested = true;
    cleanup_system_matlab();
end

%% MATLAB UTILITY FUNCTIONS

function log_sample_to_binary_matlab(timestamp, accel_data)
    % MATLAB-compliant binary logging
    global LOGGER CONFIG_GLOBAL SESSION_DATA;
    
    try
        % Check if new file needed
        if LOGGER.samples_in_file >= CONFIG_GLOBAL.samples_per_file
            close_current_binary_file_matlab();
            create_new_binary_file();
        end
        
        % Write binary data - MATLAB style
        if LOGGER.fid ~= -1
            sample_data = [timestamp, accel_data];  % 1x5 vector
            count = fwrite(LOGGER.fid, sample_data, 'double');
            
            if count == 5
                LOGGER.samples_in_file = LOGGER.samples_in_file + 1;
                LOGGER.total_samples = LOGGER.total_samples + 1;
            end
        end
        
    catch
        % Silent error
    end
end

function create_new_binary_file()
    % Create new binary file - MATLAB compliant
    global LOGGER SESSION_DATA CONFIG_GLOBAL;
    
    try
        % Create filename
        filename = sprintf('AccelData_%s_File%04d.bin', SESSION_DATA.session_id, LOGGER.file_counter);
        filepath = fullfile(SESSION_DATA.session_dir, filename);
        
        % Open binary file for writing
        LOGGER.fid = fopen(filepath, 'wb');  % 'wb' = write binary
        
        if LOGGER.fid ~= -1
            LOGGER.current_file = filepath;
            LOGGER.samples_in_file = 0;
            fprintf('Created binary file %d\n', LOGGER.file_counter);
        else
            fprintf('Warning: Failed to create file %d\n', LOGGER.file_counter);
        end
        
    catch ME
        fprintf('File creation error: %s\n', ME.message);
    end
end

function close_current_binary_file_matlab()
    % Close current binary file and create CSV companion
    global LOGGER SESSION_DATA;
    
    try
        if LOGGER.fid ~= -1
            fclose(LOGGER.fid);
            fprintf('BinFile created: %n', LOGGER.fid)
            LOGGER.fid = -1;
            
        end
        
        % Create CSV companion file
        if LOGGER.samples_in_file > 0
            % create_csv_companion_matlab();
        end
        
        LOGGER.file_counter = LOGGER.file_counter + 1;
        
    catch
        % Silent error
    end
end

function create_csv_companion_matlab()
    % Create CSV version of binary file for analysis
    global LOGGER SESSION_DATA;
    
    try
        % Read binary file back
        bin_fid = fopen(LOGGER.current_file, 'rb');
        if bin_fid == -1, return; end
        
        % Read all data
        data_matrix = fread(bin_fid, [5, LOGGER.samples_in_file], 'double');
        fclose(bin_fid);
        
        if isempty(data_matrix), return; end
        
        % Transpose to get samples as rows
        data_matrix = data_matrix';  % MATLAB transpose
        
        % Create CSV filename
        csv_filename = strrep(LOGGER.current_file, '.bin', '.csv');
        
        % Write CSV file
        csv_fid = fopen(csv_filename, 'w');
        if csv_fid == -1, return; end
        
        % Write header
        fprintf(csv_fid, 'AbsoluteTime,RelativeTime_s,Mirror_Y_g,Mirror_X_g,Mirror_Z_g,Desk_Y_g\n');
        
        % Write data
        for i = 1:size(data_matrix, 1)
            abs_time = SESSION_DATA.start_time + data_matrix(i,1)/(24*3600);
            fprintf(csv_fid, '%s,%.6f,%.6f,%.6f,%.6f,%.6f\n', ...
                datestr(abs_time, 'yyyy-mm-dd HH:MM:SS.FFF'), ...
                data_matrix(i, 1), data_matrix(i, 2), data_matrix(i, 3), ...
                data_matrix(i, 4), data_matrix(i, 5));
        end
        
        fclose(csv_fid);
        
    catch
        % Silent error
    end
end


function update_status_matlab()
    % Update status display
    global SESSION_DATA DATA_BUFFER LOGGER;
    
    try
        elapsed_hours = (now - SESSION_DATA.start_time) * 24;
        actual_rate = DATA_BUFFER.sample_count / toc(SESSION_DATA.start_tic);
        
        status_str = sprintf('%.2f hrs | %.1fM samples | %.0f Hz | File %d ', ...
            elapsed_hours, DATA_BUFFER.sample_count/1e6, actual_rate, LOGGER.file_counter);
        
        
    catch
    end
end

function cleanup_system_matlab()
    % Final cleanup - MATLAB style
    global SESSION_DATA DATA_BUFFER LOGGER;
    
    fprintf('\n=== SYSTEM CLEANUP ===\n');
    
    try
        % Stop timer
        if isfield(SESSION_DATA, 'display_timer') && isvalid(SESSION_DATA.display_timer)
            stop(SESSION_DATA.display_timer);
            delete(SESSION_DATA.display_timer);
        end
        
        % Stop DAQ
        if isfield(SESSION_DATA, 'data_listener') && isvalid(SESSION_DATA.data_listener)
            delete(SESSION_DATA.data_listener);
        end
        
        % Close current file
        close_current_binary_file_matlab();
        
        % Statistics
        runtime_hours = (now - SESSION_DATA.start_time) * 24;
        fprintf('Runtime: %.2f hours\n', runtime_hours);
        fprintf('Total samples: %.0f\n', DATA_BUFFER.sample_count);
        fprintf('Files created: %d\n', LOGGER.file_counter);
        fprintf('Session directory: %s\n', SESSION_DATA.session_dir);
        
        % Create summary
        create_session_summary_matlab();
        
    catch ME
        fprintf('Cleanup error: %s\n', ME.message);
    end
    
    
    fprintf('Shutdown complete\n');
end

function create_session_summary_matlab()
    % Create session summary file
    global SESSION_DATA DATA_BUFFER LOGGER CONFIG_GLOBAL;
    
    try
        summary_file = fullfile(SESSION_DATA.session_dir, 'session_summary.txt');
        fid = fopen(summary_file, 'w');
        if fid ~= -1
            fprintf(fid, 'SESSION SUMMARY\n');
            fprintf(fid, '==================================\n\n');
            fprintf(fid, 'Start: %s\n', datestr(SESSION_DATA.start_time));
            fprintf(fid, 'End: %s\n', datestr(now));
            fprintf(fid, 'Duration: %.2f hours\n', (now - SESSION_DATA.start_time) * 24);
            fprintf(fid, 'Samples: %.0f\n', DATA_BUFFER.sample_count);
            fprintf(fid, 'Files: %d\n', LOGGER.file_counter);
            fprintf(fid, 'Channels: %s\n', strjoin(CONFIG_GLOBAL.channel_names, ', '));
            fprintf(fid, 'Display: HH:MM:SS rolling window\n');
            fclose(fid);
        end
    catch
    end
end
function batch_convert_bin_to_csv(folder_path)
% Convert all .bin files in the specified folder to .csv format
    
    if nargin < 1
        folder_path = uigetdir(pwd, 'Select folder containing .bin files');
        if folder_path == 0
            disp('No folder selected.');
            return;
        end
    end
    
    bin_files = dir(fullfile(folder_path, '*.bin'));
    if isempty(bin_files)
        disp('No .bin files found in the folder.');
        return;
    end
    
    for k = 1:length(bin_files)
        bin_file = fullfile(folder_path, bin_files(k).name);
        fprintf('Converting %s', bin_files(k).name);
    
        fid = fopen(bin_file, 'rb');
        if fid == -1
            fprintf('Failed to open %s', bin_files(k).name);
            continue;
        end
    
        data_matrix = fread(fid, [5, inf], 'double');
        fclose(fid);
    
        if isempty(data_matrix)
            fprintf('No data in %s', bin_files(k).name);
            continue;
        end
    
        data_matrix = data_matrix';
        csv_file = strrep(bin_file, '.bin', '.csv');
        fid_csv = fopen(csv_file, 'w');
        if fid_csv == -1
            fprintf('Failed to create CSV for %s', bin_files(k).name);
            continue;
        end
    
        fprintf(fid_csv, 'AbsoluteTime,RelativeTime_s,Mirror_Y_g,Mirror_X_g,Mirror_Z_g,Desk_Y_g');
        start_time = now;
        for i = 1:size(data_matrix, 1)
            abs_time = start_time + data_matrix(i,1)/(24*3600);
            fprintf(fid_csv, '%s,%.6f,%.6f,%.6f,%.6f,%.6f', ...
                datestr(abs_time, 'yyyy-mm-dd HH:MM:SS.FFF'), ...
                data_matrix(i, 1), data_matrix(i, 2), data_matrix(i, 3), ...
                data_matrix(i, 4), data_matrix(i, 5));
        end
        fclose(fid_csv);
        fprintf('Saved CSV: %s', csv_file);
    end

fprintf('Batch conversion complete.');
end