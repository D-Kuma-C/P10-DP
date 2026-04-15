from pyproj import Transformer

input_file = r"C:\Git\P10-DP\t-drive\gps_output_p-3_d-0.05_t-15min_f-10_start-20080202_end-20080209.dat"
output_file = r"C:\Git\P10-DP\t-drive\tdrive_cartesian.dat"

transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

with open(input_file) as f:
    lines = f.readlines()

with open(output_file, "w") as out:
    for line in lines:
        line = line.strip()

        if line.startswith("#"):
            out.write(line + "\n")

        elif line.startswith(">0:"):
            points = line[3:].split(";")
            new_points = []

            for p in points:
                if not p:
                    continue

                lon, lat = map(float, p.split(","))
                x, y = transformer.transform(lon, lat)

                new_points.append(f"{x},{y}")

            out.write(">0:" + ";".join(new_points) + ";\n")

print("Conversion complete.")