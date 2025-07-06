# app.py (Updated for AJAX)

import os
import json
import time
import uuid
from flask import Flask, render_template, request, url_for, jsonify # <-- Import jsonify

# Import your existing SFS modules
from sfs_photoclinometry import io_handler, core, visualization

# --- Configuration (Unchanged) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'static', 'outputs')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)

# --- run_sfs_pipeline function (Unchanged) ---
def run_sfs_pipeline(sfs_inputs):
    # This function is exactly the same as before, returning a dictionary
    print("--- Starting Shape-from-Shading (Photoclinometry) Process ---")
    start_time = time.time()
    print(f"Loading image: {sfs_inputs['image_path']}")
    image = io_handler.load_image(sfs_inputs["image_path"])
    print("Running SFS optimization...")
    relative_dem = core.run_sfs_optimization(image, sfs_inputs)
    scaled_dem = core.scale_dem_to_meters(relative_dem, image.shape, sfs_inputs)
    output_dir = sfs_inputs["output_dir"]
    output_basename = os.path.join(output_dir, "reconstructed_dem")
    print("\n--- Saving Outputs ---")
    geotiff_path = f"{output_basename}.tif"
    obj_path = f"{output_basename}.obj"
    vis_path_2d = os.path.join(output_dir, "depth_map_visualization.png")
    vis_path_3d = os.path.join(output_dir, "surface_3d_visualization.png")
    io_handler.save_dem_as_geotiff(geotiff_path, scaled_dem, image.shape, sfs_inputs)
    io_handler.save_dem_as_obj(obj_path, scaled_dem)
    visualization.plot_depth_map(scaled_dem, save_path=vis_path_2d)
    visualization.plot_3d_surface(scaled_dem, save_path=vis_path_3d)
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total execution time: {total_time:.2f} seconds")
    return {
        "total_time": f"{total_time:.2f}", "min_height": f"{scaled_dem.min():.2f}",
        "max_height": f"{scaled_dem.max():.2f}",
        "geotiff_url": url_for('static', filename=os.path.relpath(geotiff_path, os.path.join(BASE_DIR, 'static')).replace('\\', '/')),
        "obj_url": url_for('static', filename=os.path.relpath(obj_path, os.path.join(BASE_DIR, 'static')).replace('\\', '/')),
        "depth_map_url": url_for('static', filename=os.path.relpath(vis_path_2d, os.path.join(BASE_DIR, 'static')).replace('\\', '/')),
        "surface_3d_url": url_for('static', filename=os.path.relpath(vis_path_3d, os.path.join(BASE_DIR, 'static')).replace('\\', '/'))
    }

# --- @app.route('/') is unchanged ---
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# --- @app.route('/run') is MODIFIED ---
@app.route('/run', methods=['POST'])
def run_sfs():
    """ Handles the AJAX request, runs the pipeline, and returns JSON. """
    try:
        if 'image_file' not in request.files or request.files['image_file'].filename == '':
            return jsonify({'error': 'Image file is required.'}), 400

        file = request.files['image_file']
        sfs_params = {
            "sun_azimuth_deg": float(request.form.get('sun_azimuth_deg', 101.55)),
            "sun_elevation_deg": float(request.form.get('sun_elevation_deg', 34.80)),
            "initial_surface": "flat", "regularization_lambda": 5e-3, "max_iterations": 150,
            "spacecraft_altitude_km": float(request.form.get('focal_length_mm', 95.85)),
            "focal_length_mm": float(request.form.get('focal_length_mm', 140.0)),
            "detector_pixel_width_um": 7.0,
            "refined_corner_coords": {
                "upper_left": {"lat": -0.180085, "lon": 257.530303}, "upper_right": {"lat": -0.201906, "lon": 256.909083},
                "lower_left": {"lat": 29.781694, "lon": 257.122178}, "lower_right": {"lat": 29.758136, "lon": 256.403670},
            }, "projection": "Selenographic",
        }
        
        run_id = str(uuid.uuid4())
        image_filename = f"{run_id}_{file.filename}"
        uploaded_image_path = os.path.join(UPLOAD_FOLDER, image_filename)
        file.save(uploaded_image_path)
        
        run_output_dir = os.path.join(OUTPUT_FOLDER, run_id)
        os.makedirs(run_output_dir, exist_ok=True)
        
        sfs_inputs = sfs_params.copy()
        sfs_inputs["image_path"] = uploaded_image_path
        sfs_inputs["output_dir"] = run_output_dir
        
        results = run_sfs_pipeline(sfs_inputs)
        
        # Return the results as a JSON object
        return jsonify(results)

    except Exception as e:
        print(f"An error occurred during SFS processing: {e}")
        # Return an error as a JSON object
        return jsonify({'error': f'An internal server error occurred: {e}'}), 500

if __name__ == '__main__':
    app.run(debug=True)