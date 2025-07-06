SFS_INPUTS = {
    # --- File Paths (NOW A PNG) ---
    "image_path": "data/moon1.png",  # <--- CHANGED to a PNG file
    "output_dir": "output",

    # --- Illumination Geometry (Crucial for SFS) ---
    "sun_azimuth_deg": 101.554510,
    "sun_elevation_deg": 34.802249,

    # --- SFS Algorithm Parameters ---
    "initial_surface": "flat",
    "regularization_lambda": 5e-3,
    "max_iterations": 150,

    # --- Georeferencing & Scaling (Provided externally, not from image file) ---
    "spacecraft_altitude_km": 95.85,
    "focal_length_mm": 140.0,
    "detector_pixel_width_um": 7.0,
    "refined_corner_coords": {
        "upper_left":    {"lat": -0.180085, "lon": 257.530303},
        "upper_right":   {"lat": -0.201906, "lon": 256.909083},
        "lower_left":    {"lat": 29.781694, "lon": 257.122178},
        "lower_right":   {"lat": 29.758136, "lon": 256.403670},
    },
    "projection": "Selenographic",
}