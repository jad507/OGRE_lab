import ast
import csv
import os

# Read the contents of the text file
with open("framerate_results.txt", "r") as file:
    lines = file.readlines()

# Parse each line into a dictionary
data = [ast.literal_eval(line.strip()) for line in lines]

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
