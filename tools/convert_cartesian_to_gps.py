from pyproj import Transformer

input_file = r"C:\Users\test\Desktop\Uni\P10-DP\AdaTrace\porto_20k.dat-eps1.0-iteration0.dat"
output_file = r"C:\Users\test\Desktop\Uni\P10-DP\trajectory_similarity\data\synthetic\porto_20k.dat-eps1.0-iteration0.dat"

# IMPORTANT:
# Use the same CRS as the GPS -> x,y conversion.
# For Porto, we used UTM zone 29N.
transformer = Transformer.from_crs("EPSG:32629", "EPSG:4326", always_xy=True)

# IMPORTANT:
# Paste the exact min_x and min_y printed by your GPS -> x,y conversion script.
# Example:
# min_x used for shift: 531234.123
# min_y used for shift: 4556789.456
MIN_X = 0.0  # replace with your printed min_x
MIN_Y = 0.0  # replace with your printed min_y

# Optional:
# AdaTrace output usually does not contain timestamps.
# If you want to preserve the same output format as before:
# lon,lat,timestamp
# then use a placeholder timestamp.
# 1970-01-01 00:00:00
PLACEHOLDER_TIMESTAMP = ""


with open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

with open(output_file, "w", encoding="utf-8") as out:
    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line.startswith("#"):
            # Preserve trajectory ID line.
            out.write(line + "\n")

        elif line.startswith(">0:"):
            points = line[3:].split(";")
            converted_points = []

            for p in points:
                p = p.strip()
                if not p:
                    continue

                parts = p.split(",")

                if len(parts) < 2:
                    continue

                shifted_x = float(parts[0])
                shifted_y = float(parts[1])

                # Undo local shift.
                x = shifted_x + MIN_X
                y = shifted_y + MIN_Y

                # Convert projected x,y back to lon,lat.
                lon, lat = transformer.transform(x, y)

                if PLACEHOLDER_TIMESTAMP:
                    converted_points.append(
                        f"{lon:.6f},{lat:.6f},{PLACEHOLDER_TIMESTAMP}"
                    )
                else:
                    converted_points.append(
                        f"{lon:.6f},{lat:.6f}"
                    )

            out.write(">0:" + ";".join(converted_points) + ";\n")

print("Reverse conversion complete.")