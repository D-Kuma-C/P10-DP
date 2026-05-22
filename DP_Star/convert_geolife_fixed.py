

import os

src = "data/Geolife Trajectories 1.3/Data"
dst = "data/Geolife Trajectories 1.3/Trajectories"

os.makedirs(dst, exist_ok=True)

count = 0

for user in os.listdir(src):
    traj_dir = os.path.join(src, user, "Trajectory")

    if not os.path.exists(traj_dir):
        continue

    for file in os.listdir(traj_dir):
        if not file.endswith(".plt"):
            continue

        input_file = os.path.join(traj_dir, file)

        with open(input_file) as f:
            lines = f.readlines()[6:]  # skip header

        output = []

        for line in lines:
            parts = line.strip().split(",")

            try:
                lat = float(parts[0])
                lon = float(parts[1])

                # filter invalid values
                if 39 <= lat <= 41 and 115 <= lon <= 117:
                    output.append(f"{lat},{lon}\n")

            except:
                continue

        if len(output) < 2:
            continue

        with open(f"{dst}/{count}.txt", "w") as f:
            f.writelines(output)

        count += 1

print("Converted:", count)