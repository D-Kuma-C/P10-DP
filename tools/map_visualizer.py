import folium

BEIJING = [39.9, 116]
PORTO = [41.15, -8.62]

MAX_TRAJECTORIES = 20000

m = folium.Map(location=PORTO, zoom_start=11, tiles="CartoDB positron", prefer_canvas=True)

def plot_file(file_path, color="blue", max_traj=None, tiles="CartoDB positron"):
    

    traj = []
    count = 0
    with open(file_path) as f:
        for line in f:
            line = line.strip()

            if line.startswith("#"):
                if traj:
                    folium.PolyLine(traj, color=color, weight=1, opacity=0.2).add_to(m)
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
                weight=1,
                opacity=0.2
            ).add_to(m)
    
    print("Trajectory count: ", count)
    

plot_file(r"/input/dpstar_synthetic/eps_0.1/test.dat", max_traj=MAX_TRAJECTORIES, color="blue")

m.save(r"C:\Users\test\Desktop\Uni\P10-DP\output\testing2.html")