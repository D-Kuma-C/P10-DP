import folium

BEIJING = [39.9, 116]
PORTO = [41.15, -8.62]

MAX_TRAJECTORIES = 20000

m = folium.Map(location=BEIJING, zoom_start=11, tiles="CartoDB VoyagerNoLabels", prefer_canvas=True)

def plot_file(file_path, color="blue", max_traj=None):
    

    traj = []
    count = 0
    with open(file_path) as f:
        for line in f:
            line = line.strip()

            if line.startswith("#"):
                if traj:
                    folium.PolyLine(traj, color=color, weight=2, opacity=1).add_to(m)
                    traj = []
                    count += 1
                    if max_traj and (count > max_traj):
                        break
            elif line.startswith(">0:"):
                points = line[3:].split(";")
                for p in points:
                    if p:
                        coords = p.split(",")
                        lon = float(coords[0])
                        lat = float(coords[1])

                        traj.append((lat, lon))
    
        if traj:
            folium.PolyLine(
                traj,
                color=color,
                weight=2,
                opacity=1
            ).add_to(m)
    
    print("Trajectory count: ", count)
    

plot_file(r"C:\Git\P10-DP\data\testdata.dat", max_traj=MAX_TRAJECTORIES, color="blue")

m.save(r"C:\Git\P10-DP\map-output\example.html")
