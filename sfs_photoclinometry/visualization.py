import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def plot_depth_map(dem: np.ndarray, save_path: str):
    """Creates and saves a 2D colorized plot of the DEM."""
    plt.figure(figsize=(10, 8))
    plt.imshow(dem, cmap='terrain')
    plt.title("Reconstructed DEM (Depth Map)")
    plt.xlabel("X (pixels)")
    plt.ylabel("Y (pixels)")
    cbar = plt.colorbar()
    cbar.set_label("Height (meters)")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()

def plot_3d_surface(dem: np.ndarray, save_path: str):
    """Creates and saves a 3D surface plot of the DEM."""
    height, width = dem.shape
    X, Y = np.meshgrid(np.arange(width), np.arange(height))

    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Use a stride to plot large images faster
    stride = max(1, int(min(height, width) / 200))
    surf = ax.plot_surface(X, Y, dem, cmap='terrain', rstride=stride, cstride=stride,
                           linewidth=0, antialiased=False)

    ax.set_title("Reconstructed 3D Surface", fontsize=16)
    ax.set_xlabel("X (pixels)")
    ax.set_ylabel("Y (pixels)")
    ax.set_zlabel("Height (meters)")
    
    # Make aspect ratio more realistic
    ax.set_box_aspect((width, height, 0.3 * max(width, height)))

    fig.colorbar(surf, shrink=0.6, aspect=10, label="Height (meters)")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()