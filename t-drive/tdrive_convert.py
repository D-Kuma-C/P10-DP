# t-drive eks:
# 1,2008-02-02 15:36:08,116.51172,39.92123
# 1,2008-02-02 15:46:08,116.51135,39.93883

# output eks:
# #1:
# >0:116.51172,39.92123;116.51135,39.93883;

import os

input_folder = r"C:\p10-data\taxi_log_2008_by_id"
output_file = r"C:\Git\P10-DP\t-drive\output.dat"

def load_files(start, end):
    files = [f for f in os.listdir(input_folder) if f.endswith(".txt")]
    files.sort(key=lambda x: int(x.split(".")[0]))

    open(output_file, "w").close()

    for index in range(start, end):
        if index < len(files):
            load_data(files[index])

def load_data(file):

    file_path = os.path.join(input_folder, file)

    with open(file_path) as f:
        lines = f.readlines()

    trajectory = []
    id = "#" + lines[0].split(',')[0]
    for line in lines:
        test = line.strip().split(',')
        if (f"{test[2]},{test[3]}" == "0.0,0.0"):
            continue
        trajectory.append(f"{test[2]},{test[3]}")
    
    trajectory_string = ";".join(trajectory) + ";"

    with open(output_file, "a") as f2:
        f2.write(id + "\n")
        f2.write(f">0:{trajectory_string}\n")


load_files(0, 150)