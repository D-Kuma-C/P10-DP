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

    plt.hexbin(lons, lats, gridsize=20, vmin=0, vmax=600)
    plt.colorbar(label="Density")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()

# Original
plot_heatmap(r"C:\Git\P10-DP\PrivTrace-main\datasets\porto_lines-1000_p-3_d-0.05_s-40_t-15min_start-20130107_end-20140630.dat")

# Generated
plot_heatmap(r"C:\Git\P10-DP\PrivTrace-main\generated_tras.txt")