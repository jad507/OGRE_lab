import ast
import csv
import os

# Read the contents of the text file
with open("framerate_results.txt", "r", encoding="utf-8") as file:
    lines = file.readlines()

# Parse each line into a dictionary, modifying the fields to match excel sheet
data = []
for line in lines:
    entry = ast.literal_eval(line.strip())
    entry["folder"] = os.path.basename(entry["folder"])
    entry["first_file"] = os.path.splitext(os.path.basename(entry["first_file"]))[0]
    entry["last_file"] = os.path.splitext(os.path.basename(entry["last_file"]))[0]
    entry["time_diff_seconds"] = float(str(entry["time_diff_seconds"]).lstrip("'"))
    entry["framerate"] = float(str(entry["framerate"]).lstrip("'"))

    data.append(entry)


# Define the CSV file name
csv_filename = "framerate_results_converted.csv"

# Write the data to a CSV file
with open(csv_filename, "w", newline='', encoding='utf-8') as csvfile:
    fieldnames = ["folder", "subfolder", "first_file", "last_file", "num_files", "time_diff_seconds", "framerate"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for entry in data:
        writer.writerow(entry)

print(f"Data successfully converted to {csv_filename}.")
