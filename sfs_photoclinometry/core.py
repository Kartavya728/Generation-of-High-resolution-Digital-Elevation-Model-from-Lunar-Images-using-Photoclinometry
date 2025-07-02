import numpy as np
from scipy.optimize import minimize
from scipy.ndimage import laplace
from tqdm import tqdm
from . import utils

# Use a class to manage optimization state cleanly
class SFSCallback:
    def __init__(self, max_iter):
        self.pbar = tqdm(total=max_iter, desc="L-BFGS-B Optimization")
        self.iteration = 0

    def __call__(self, xk):
        self.pbar.update(1)
        self.iteration += 1
    
    def close(self):
        self.pbar.close()

def sfs_cost_and_gradient(Z_flat, observed_image, light_vec, lambda_reg, shape):
    """
    Calculates cost and gradient for a single-step optimization.
    This is the core function passed to the SciPy optimizer.
    """
    # --- Reshape Z from flat to 2D ---
    Z = Z_flat.reshape(shape)

    # --- 1. Brightness Cost Term (like C++ e1) ---
    predicted_image = utils.calculate_predicted_image(Z, light_vec)
    brightness_error = observed_image - predicted_image
    brightness_cost = 0.5 * np.sum(brightness_error**2)

    # --- 2. Smoothness Cost Term (replaces C++ e3) ---
    laplacian_Z = laplace(Z, mode='constant', cval=0.0)
    smoothness_cost = 0.5 * np.sum(laplacian_Z**2)
    
    # --- 3. Total Cost ---
    total_cost = brightness_cost + lambda_reg * smoothness_cost
    
    # --- 4. Gradient of the Cost Function ---
    # Gradient = d(Cost)/dZ = d(brightness_cost)/dZ + lambda * d(smoothness_cost)/dZ
    
    # Gradient of brightness term (complex derivation using chain rule)
    p, q = np.gradient(Z)
    denom = (1 + p**2 + q**2)**1.5
    # Avoid division by zero
    denom[denom < 1e-9] = 1e-9
    
    term_p = light_vec[0] - light_vec[2] * p
    term_q = light_vec[1] - light_vec[2] * q
    
    # Partial derivatives of the error term w.r.t p and q
    dE_dp = brightness_error * (term_p / denom)
    dE_dq = brightness_error * (term_q / denom)
    
    # The gradient d(Cost)/dZ is the divergence of (dE/dp, dE/dq)
    # We use negative gradient because np.gradient's convention
    _, d_dx = np.gradient(dE_dp)
    d_dy, _ = np.gradient(dE_dq)
    brightness_gradient = -(d_dx + d_dy)

    # Gradient of smoothness term: lambda * ∇²(∇²Z) (bi-Laplacian)
    smoothness_gradient = laplace(laplacian_Z, mode='constant', cval=0.0)

    # --- Total Gradient ---
    total_gradient = brightness_gradient + lambda_reg * smoothness_gradient
    
    return total_cost, total_gradient.flatten()

def run_sfs_optimization(image: np.ndarray, config: dict):
    """Orchestrates and runs the L-BFGS-B optimization."""
    height, width = image.shape
    
    # 1. Get Light Vector from illumination geometry
    light_vec = utils.get_light_vector(
        config["sun_azimuth_deg"], config["sun_elevation_deg"]
    )
    print(f"Calculated Light Vector (X,Y,Z): {np.round(light_vec, 3)}")
    
    # 2. Initialize Height Map (Z)
    if config["initial_surface"] == "flat":
        Z_initial = np.zeros(image.shape, dtype=np.float32)
    else:
        # Placeholder for loading a coarse DEM
        raise NotImplementedError("Loading initial DEM not yet implemented.")

    # 3. Setup optimizer
    callback = SFSCallback(config["max_iterations"])
    
    result = minimize(
        fun=sfs_cost_and_gradient,
        x0=Z_initial.flatten(),
        args=(image, light_vec, config["regularization_lambda"], image.shape),
        method='L-BFGS-B',
        jac=True,  # Our function returns both cost and gradient
        options={'maxiter': config["max_iterations"], 'disp': False}, # disp=False to use our own progress bar
        callback=callback
    )
    callback.close()
    
    if not result.success:
        print(f"WARNING: Optimizer did not converge. Reason: {result.message}")
        
    # 4. Reshape final result to a 2D DEM
    final_dem = result.x.reshape(image.shape)
    
    return final_dem

def scale_dem_to_meters(dem: np.ndarray, shape: tuple, config: dict) -> np.ndarray:
    """Scales the relative DEM to physical units (meters)."""
    # Calculate pixel scale (meters per pixel)
    pixel_size_m = (config["detector_pixel_width_um"] * 1e-6) * \
                   (config["spacecraft_altitude_km"] * 1000) / \
                   (config["focal_length_mm"] * 1e-3)
    
    print(f"\nEstimated pixel scale: {pixel_size_m:.2f} m/pixel")
    
    # The output of SFS is Z/pixel_scale. To get Z, multiply by pixel_scale.
    scaled_dem = dem * pixel_size_m
    
    # Center the DEM around zero height
    scaled_dem -= np.mean(scaled_dem)
    
    return scaled_dem