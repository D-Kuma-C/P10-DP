from pyproj import Transformer
import folium


# ============================================================
# CONFIG
# ============================================================

# Input .dat file with x,y points
INPUT_FILE = r"C:\Users\test\Desktop\Uni\P10-DP\AdaTrace\porto_20k.dat"

# Output HTML map
OUTPUT_HTML = r"C:\Users\test\Desktop\Uni\P10-DP\boundingRectangle\porto_20k_bounding_rectangle1.html"

# CRS of the x,y coordinates in the .dat file
# Examples:
#   "EPSG:3857"  -> Web Mercator
#   "EPSG:32629" -> UTM zone 29N (recommended for Porto)
SOURCE_CRS = "EPSG:32629"

# If your x,y data was shifted to local coordinates, set these to the same
# min_x and min_y used during conversion. Otherwise keep them at 0.0.
SHIFT_X = 0.0
SHIFT_Y = 0.0


# ============================================================
# PARSE DAT FILE
# ============================================================

def read_xy_points_from_dat(file_path):
    points = []

    with open(file_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()

            if not line:
                continue

            if line.startswith(">0:"):
                point_text = line[3:]
                raw_points = point_text.split(";")

                for p in raw_points:
                    p = p.strip()
                    if not p:
                        continue

                    parts = p.split(",")

                    # Supports both:
                    #   x,y
                    #   x,y,time
                    if len(parts) < 2:
                        continue

                    x = float(parts[0]) + SHIFT_X
                    y = float(parts[1]) + SHIFT_Y
                    points.append((x, y))

    return points


# ============================================================
# MAIN
# ============================================================

def main():
    points = read_xy_points_from_dat(INPUT_FILE)

    if not points:
        raise ValueError("No points found in input file.")

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    min_x = min(xs)
    max_x = max(xs)
    min_y = min(ys)
    max_y = max(ys)

    print("Bounding rectangle in x,y coordinates:")
    print(f"min_x = {min_x}")
    print(f"max_x = {max_x}")
    print(f"min_y = {min_y}")
    print(f"max_y = {max_y}")

    # Convert projected x,y -> lon,lat
    transformer = Transformer.from_crs(SOURCE_CRS, "EPSG:4326", always_xy=True)

    # Rectangle corners in x,y
    # bottom-left, bottom-right, top-right, top-left
    corners_xy = [
        (min_x, min_y),
        (max_x, min_y),
        (max_x, max_y),
        (min_x, max_y),
    ]

    # Convert to (lat, lon) for folium
    corners_latlon = []
    for x, y in corners_xy:
        lon, lat = transformer.transform(x, y)
        corners_latlon.append((lat, lon))

    print("\nBounding rectangle corners in lat/lon:")
    labels = ["bottom-left", "bottom-right", "top-right", "top-left"]
    for label, (lat, lon) in zip(labels, corners_latlon):
        print(f"{label}: lat={lat}, lon={lon}")

    # Map center = center of rectangle
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    center_lon, center_lat = transformer.transform(center_x, center_y)

    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="OpenStreetMap")

    # Draw only the rectangle
    folium.Rectangle(
        bounds=[
            [corners_latlon[0][0], corners_latlon[0][1]],  # bottom-left
            [corners_latlon[2][0], corners_latlon[2][1]],  # top-right
        ],
        color="red",
        weight=3,
        fill=True,
        fill_opacity=0.15,
        popup=(
            f"Bounding Rectangle<br>"
            f"min_x={min_x:.3f}<br>"
            f"max_x={max_x:.3f}<br>"
            f"min_y={min_y:.3f}<br>"
            f"max_y={max_y:.3f}"
        ),
    ).add_to(m)

    # Save map
    m.save(OUTPUT_HTML)
    print(f"\nSaved map to: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
