import folium

BEIJING = [39.9, 116]
PORTO = [41.15, -8.62]

m = folium.Map(location=PORTO, zoom_start=11, tiles="CartoDB positron")

def plot_file(file_path, color="blue", max_traj=None, tiles="CartoDB positron"):
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
                if max_traj and (count > max_traj):
                    break
        elif line.startswith(">0:"):
            points = line[3:].split(";")
            for p in points:
                if p:
                    lon, lat = map(float, p.split(","))
                    traj.append((lat, lon))
    
    print("Trajectory count: ", count)
    

plot_file(r"C:\Git\P10-DP\PrivTrace-main\generated_tras.txt", color="blue")

m.save(f"index_porto_gen.html")