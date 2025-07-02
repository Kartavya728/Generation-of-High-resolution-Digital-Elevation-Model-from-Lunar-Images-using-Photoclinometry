import numpy as np

def get_light_vector(sun_azimuth_deg: float, sun_elevation_deg: float) -> np.ndarray:
    """
    Converts sun azimuth and elevation to a 3D unit light vector.
    Coordinate system: +X East, +Y North, +Z Up.
    Azimuth is clockwise from North.
    """
    az_rad = np.deg2rad(sun_azimuth_deg)
    el_rad = np.deg2rad(sun_elevation_deg)

    z = np.sin(el_rad)
    xy_proj = np.cos(el_rad)
    x = xy_proj * np.sin(az_rad)  # East
    y = xy_proj * np.cos(az_rad)  # North
    
    light_vec = np.array([x, y, z])
    return light_vec / np.linalg.norm(light_vec)


def calculate_surface_normals(Z: np.ndarray) -> np.ndarray:
    """Calculates surface normal vectors from the height map Z."""
    # Note: np.gradient returns (dy, dx) which corresponds to (q, p)
    q, p = np.gradient(Z)
    
    # Normal vector is (-p, -q, 1), then normalized.
    normals = np.stack([-p, -q, np.ones_like(Z)], axis=-1)
    
    # Calculate norms, keeping the last dimension for broadcasting
    norms = np.linalg.norm(normals, axis=2, keepdims=True)
    
    # --- THIS IS THE CORRECTED PART ---
    # To avoid division by zero for flat areas where norm is zero,
    # we create a safe version of the norms. We'll set any norm
    # smaller than a tiny epsilon to 1.0. This is safe because if the
    # norm is zero, the original normal vector was [0, 0, 0] anyway.
    safe_norms = np.maximum(norms, 1e-9)
    
    # Normalize each vector using broadcasting.
    # NumPy automatically handles dividing an (h, w, 3) array
    # by an (h, w, 1) array.
    normalized_normals = normals / safe_norms
    
    return normalized_normals

def calculate_predicted_image(Z: np.ndarray, light_vec: np.ndarray) -> np.ndarray:
    """Calculates the predicted image using the Lambertian reflectance model."""
    normals = calculate_surface_normals(Z)
    # Lambertian model: I = albedo * max(0, L · N)
    # We assume albedo=1 is baked into the observed image normalization.
    reflectance = np.dot(normals, light_vec)
    return np.maximum(0, reflectance)