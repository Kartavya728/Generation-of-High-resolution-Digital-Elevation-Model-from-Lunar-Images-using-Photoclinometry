import os
import time
from sfs_photoclinometry import io_handler, core, visualization

# --- USER INPUTS ---
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

def main():
    """Main function to run the Shape-from-Shading photoclinometry pipeline."""
    print("--- Starting Advanced Shape-from-Shading (Photoclinometry) Process ---")
    start_time = time.time()

    os.makedirs(SFS_INPUTS["output_dir"], exist_ok=True)
    print(f"Output will be saved to: {SFS_INPUTS['output_dir']}")

    print(f"Loading image: {SFS_INPUTS['image_path']}")
    try:
        # The load_image call now returns only the image array
        image = io_handler.load_image(SFS_INPUTS["image_path"]) # <--- MODIFIED
    except FileNotFoundError:
        print(f"ERROR: Input image not found at {SFS_INPUTS['image_path']}")
        print("Please place the image in the 'data/' directory.")
        return

    print("Running SFS optimization...")
    relative_dem = core.run_sfs_optimization(image, SFS_INPUTS)
    
    scaled_dem = core.scale_dem_to_meters(relative_dem, image.shape, SFS_INPUTS)

    output_basename = os.path.join(SFS_INPUTS["output_dir"], "reconstructed_dem")
    print("\n--- Saving Outputs ---")

    print(f"Saving GeoTIFF DEM to: {output_basename}.tif")
    io_handler.save_dem_as_geotiff(f"{output_basename}.tif", scaled_dem, image.shape, SFS_INPUTS)

    print(f"Saving OBJ 3D model to: {output_basename}.obj")
    io_handler.save_dem_as_obj(f"{output_basename}.obj", scaled_dem)

    vis_path_2d = os.path.join(SFS_INPUTS["output_dir"], "depth_map_visualization.png")
    print(f"Saving 2D depth map visualization to: {vis_path_2d}")
    visualization.plot_depth_map(scaled_dem, save_path=vis_path_2d)

    vis_path_3d = os.path.join(SFS_INPUTS["output_dir"], "surface_3d_visualization.png")
    print(f"Saving 3D surface visualization to: {vis_path_3d}")
    visualization.plot_3d_surface(scaled_dem, save_path=vis_path_3d)

    print("\n--- Process Finished ---")
    end_time = time.time()
    print(f"Total execution time: {end_time - start_time:.2f} seconds")
    print(f"Reconstructed Surface Height (in meters):")
    print(f"  - Minimum Height: {scaled_dem.min():.2f} m")
    print(f"  - Maximum Height: {scaled_dem.max():.2f} m")
    print("--------------------------\n")

if __name__ == "__main__":
    main()