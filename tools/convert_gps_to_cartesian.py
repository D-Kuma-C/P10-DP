from pyproj import Transformer

input_file = r"C:\Users\test\Desktop\Uni\P10-DP\trajectory_similarity\data\original\porto_time_lines-20000_p-3_d-0.05_s-40_t-15min_start-20130107_end-20140630.dat"
output_file = r"C:\Users\test\Desktop\Uni\P10-DP\AdaTrace\porto_20k.dat"

# WGS84 lon/lat -> Web Mercator x/y
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

with open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

with open(output_file, "w", encoding="utf-8") as out:
    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line.startswith("#"):
            out.write(line + "\n")

        elif line.startswith(">0:"):
            points = line[3:].split(";")
            new_points = []

            for p in points:
                p = p.strip()
                if not p:
                    continue

                parts = p.split(",")

                if len(parts) < 2:
                    continue

                lon = float(parts[0])
                lat = float(parts[1])

                x, y = transformer.transform(lon, lat)

                # AdaTrace input: x,y only
                new_points.append(f"{x},{y}")

            out.write(">0:" + ";".join(new_points) + ";\n")

print("Conversion complete.")