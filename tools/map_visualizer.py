import folium

m = folium.Map(location=[39.9, 116], zoom_start=11)

def plot_file(file_path, color="blue", max_traj=5000000000):
    with open(file_path) as f:
        lines = f.readlines()

    traj = []
    count = 0

    for line in lines:
        line = line.strip()

        if line.startswith("#"):
            if traj:
                folium.PolyLine(traj, color=color, weight=2, opacity=0.6).add_to(m)
                traj = []
                count += 1
                if count > max_traj:
                    break
        elif line.startswith(">0:"):
            points = line[3:].split(";")
            for p in points:
                if p:
                    lon, lat = map(float, p.split(","))
                    traj.append((lat, lon))
    
    print("Trajectory count: ", count)
    

plot_file(r"C:\Git\P10-DP\t-drive\output2.dat", color="blue")

m.save(f"index.html")