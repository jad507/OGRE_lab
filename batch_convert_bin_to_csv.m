
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
    fprintf('Converting %s...
', bin_files(k).name);

    fid = fopen(bin_file, 'rb');
    if fid == -1
        fprintf('Failed to open %s
', bin_files(k).name);
        continue;
    end

    data_matrix = fread(fid, [5, inf], 'double');
    fclose(fid);

    if isempty(data_matrix)
        fprintf('No data in %s
', bin_files(k).name);
        continue;
    end

    data_matrix = data_matrix';
    csv_file = strrep(bin_file, '.bin', '.csv');
    fid_csv = fopen(csv_file, 'w');
    if fid_csv == -1
        fprintf('Failed to create CSV for %s
', bin_files(k).name);
        continue;
    end

    fprintf(fid_csv, 'AbsoluteTime,RelativeTime_s,Mirror_Y_g,Mirror_X_g,Mirror_Z_g,Desk_Y_g
');
    start_time = now;
    for i = 1:size(data_matrix, 1)
        abs_time = start_time + data_matrix(i,1)/(24*3600);
        fprintf(fid_csv, '%s,%.6f,%.6f,%.6f,%.6f,%.6f
', ...
            datestr(abs_time, 'yyyy-mm-dd HH:MM:SS.FFF'), ...
            data_matrix(i, 1), data_matrix(i, 2), data_matrix(i, 3), ...
            data_matrix(i, 4), data_matrix(i, 5));
    end
    fclose(fid_csv);
    fprintf('Saved CSV: %s
', csv_file);
end

fprintf('Batch conversion complete.
');
end
