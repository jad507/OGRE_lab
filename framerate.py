import os
import datetime
import csv

from docutils.nodes import field_name


def calculate_framerate(folder_path):
    # Iterate through each subfolder in the main folder
    results = []
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

            result = {
                "folder": folder_path,
                "subfolder": subfolder,
                "first_file": first_file,
                "last_file": last_file,
                "num_files": len(files),
                "time_diff_seconds": time_diff,
                "framerate": framerate
            }

            print(result)
            results.append(result)
    return results


# Set the path to the main folder
# use os.chdir(path) to navigate in python console
# main_folder = "reverse telescope test"
# calculate_framerate(main_folder)


#to run in from windows console do
# from framerate import calculate_framerate
# calculate_framerate(r"Z:/Reverse Telescope Test/20250925")


if __name__ == "__main__":
    fullresult = []
    for folder in os.listdir(r"Z:/Reverse Telescope Test"):
        this_folder = os.path.join(r"Z:/Reverse Telescope Test", folder)
        if os.path.isdir(this_folder):
            fullresult.append(calculate_framerate(this_folder))
    with open("framerate.csv", "w", newline="") as csvfile:
        fieldnames = ["folder", "subfolder", "first_file", "last_file", "num_files", "time_diff_seconds", "framerate"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for item in fullresult:
            writer.writerow(fullresult)