


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

        with open(os.path.join(traj_dir, file)) as f:
            lines = f.readlines()[6:]  # skip header

        out = []
        for line in lines:
            parts = line.strip().split(",")
            lat = parts[0]
            lon = parts[1]
            out.append(f"{lat},{lon}\n")

        with open(f"{dst}/{count}.txt", "w") as f:
            f.writelines(out)

        count += 1

print("Converted:", count)