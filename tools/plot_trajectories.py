import matplotlib.pyplot as plt

def load_trajectories(file_path):
    trajectories = []
    with open(file_path, 'r') as f:
        lines = f.readlines()

    current_traj = []
    for line in lines:
        line = line.strip()
        if line.startswith('#'):
            if current_traj:
                trajectories.append(current_traj)
                current_traj = []
        elif line.startswith(">0:"):
            points = line[3:].split(";")
            for p in points:
                if p:
                    x, y = map(float, p.split(","))
                    current_traj.append((x, y))
    
    if current_traj:
        trajectories.append(current_traj)

    return trajectories

def plot_trajectories(trajectories, title):
    for traj in trajectories:
        x = [p[0] for p in traj]
        y = [p[1] for p in traj]
        plt.plot(x, y, alpha=0.5)

    plt.title(title)
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.grid()
    plt.show()

original_file = r"C:\Git\P10-DP\t-drive\gps_output_p-3_d-0.05_t-15min_f-10_start-20080202_end-20080209.dat"
cartesian_file = r"C:\Git\P10-DP\t-drive\tdrive_cartesian.dat"
#generated_file = "generated_tras.txt"

original = load_trajectories(original_file)
cartesian = load_trajectories(cartesian_file)
#generated = load_trajectories(generated_file)

plot_trajectories(original, "Original")
plot_trajectories(cartesian, "Cartesian")