import os
import datetime

def calculate_framerate(folder_path):
    # Iterate through each subfolder in the main folder
    for subfolder in sorted(os.listdir(folder_path)):
        subfolder_path = os.path.join(folder_path, subfolder)
        if os.path.isdir(subfolder_path):
            files = [os.path.join(subfolder_path, f) for f in os.listdir(subfolder_path) if os.path.isfile(os.path.join(subfolder_path, f))]
            if len(files) < 2:
                print(f"Skipping {subfolder}: not enough files to calculate framerate.")
                continue

            # Sort files by creation time
            files.sort(key=lambda x: os.path.getmtime(x))
            first_file = files[0]
            last_file = files[-1]

            # Get creation times
            first_time = os.path.getmtime(first_file)
            last_time = os.path.getmtime(last_file)

            # Calculate time difference in seconds
            time_diff = last_time - first_time
            num_files = len(files)

            if time_diff == 0:
                print(f"Skipping {subfolder}: time difference is zero.")
                continue

            framerate = (num_files - 1) / time_diff

            print(f"Folder: {subfolder}")
            print(f"  First file: {os.path.basename(first_file)}")
            print(f"  Last file: {os.path.basename(last_file)}")
            print(f"  Number of files: {num_files}")
            print(f"  Time difference (s): {time_diff:.2f}")
            print(f"  Framerate: {framerate:.2f} frames/sec or {framerate *60:.2f} frames/min\n")

# Set the path to the main folder
# use os.chdir(path) to navigate in python console
# main_folder = "reverse telescope test"
# calculate_framerate(main_folder)


#to run in from windows console do
# from framerate import calculate_framerate
# calculate_framerate(r"Z:/Reverse Telescope Test/20250925")