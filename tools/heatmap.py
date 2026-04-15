import matplotlib.pyplot as plt

def plot_heatmap(file_path):
    lons, lats = [], []

    with open(file_path) as f:
        for line in f:
            if line.startswith(">0:"):
                points = line[3:].strip().split(";")
                for p in points:
                    if p:
                        lon, lat = map(float, p.split(","))
                        lons.append(lon)
                        lats.append(lat)

    plt.hexbin(lons, lats, gridsize=60)
    plt.colorbar(label="Density")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()

# Original
plot_heatmap(r"C:\Git\P10-DP\t-drive\tdrive_1.dat")

# Generated
plot_heatmap(r"C:\Git\P10-DP\t-drive\tdrive_result1.txt")