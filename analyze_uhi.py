import os
import json
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.mask import mask
import geopandas as gpd
from shapely.geometry import Polygon
import matplotlib.pyplot as plt

# This scripts is heavily commented to explain each step of the Urban Heat Island analysis.
DATA_DIR = 'data'
LST_FILE = os.path.join(DATA_DIR, 'mock_lst.tif')
BOUNDARIES_FILE = os.path.join(DATA_DIR, 'city_boundaries.geojson')
# Spatial dimensions
RASTER_SIZE = 100
PIXEL_SIZE = 100  # meters
# Coordinate system (Pseudo-Mercator for web maps)
CRS = 'EPSG:3857'

def generate_mock_data():
    """Generates mock LST raster and city boundaries GeoJSON."""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    print("Generating mock Land Surface Temperature (LST) data...")
    
    # 1. Create Mock LST Raster (Simulate a cool rural area and a hot urban center)
    
    # Create a base temperature array (Rural: 25C)
    lst_array = np.ones((RASTER_SIZE, RASTER_SIZE), dtype=rasterio.float32) * 298.15 # 25C in Kelvin
    
    # Define an urban center (40x40 pixel block in the middle)
    urban_start = RASTER_SIZE // 2 - 20
    urban_end = RASTER_SIZE // 2 + 20
    
    # Add heat to the urban center (Urban: 32C, a +7K difference)
    lst_array[urban_start:urban_end, urban_start:urban_end] += 7.0 
    
    # Define the bounds and transform
    xmin, ymin = 0, 0
    xmax, ymax = RASTER_SIZE * PIXEL_SIZE, RASTER_SIZE * PIXEL_SIZE
    transform = from_bounds(xmin, ymin, xmax, ymax, RASTER_SIZE, RASTER_SIZE)
    
    # Write the mock LST to a GeoTIFF
    with rasterio.open(
        LST_FILE, 'w', driver='GTiff',
        height=RASTER_SIZE, width=RASTER_SIZE,
        count=1, dtype=rasterio.float32,
        crs=CRS, transform=transform,
        nodata=-9999
    ) as dst:
        dst.write(lst_array, 1)

    print(f"Mock LST raster saved to {LST_FILE}")

    # 2. Create Mock City Boundary GeoJSON
    
    # Define the urban polygon coordinates (slightly smaller than the heat zone)
    # The coordinates are in the same CRS as the raster
    city_polygon = Polygon([
        (urban_start * PIXEL_SIZE + 500, urban_start * PIXEL_SIZE + 500),
        (urban_end * PIXEL_SIZE - 500, urban_start * PIXEL_SIZE + 500),
        (urban_end * PIXEL_SIZE - 500, urban_end * PIXEL_SIZE - 500),
        (urban_start * PIXEL_SIZE + 500, urban_end * PIXEL_SIZE - 500),
        (urban_start * PIXEL_SIZE + 500, urban_start * PIXEL_SIZE + 500)
    ])

    # Create a GeoDataFrame
    gdf = gpd.GeoDataFrame(
        [{'name': 'Mock City', 'area_type': 'Urban'}], 
        geometry=[city_polygon], 
        crs=CRS
    )
    
    # Save to GeoJSON
    gdf.to_file(BOUNDARIES_FILE, driver='GeoJSON')
    print(f"Mock city boundaries GeoJSON saved to {BOUNDARIES_FILE}")

def analyze_uhi():
    """Performs the Urban Heat Island analysis."""
    
    # Load Data
    urban_gdf = gpd.read_file(BOUNDARIES_FILE)
    
    with rasterio.open(LST_FILE) as src:
        # 1. Calculate Urban LST (Mask the raster by the city polygon)
        # We need the geometry list from the GeoDataFrame
        urban_geom = urban_gdf.geometry.values
        
        # Mask the raster
        urban_data, urban_transform = mask(src, urban_geom, crop=True)
        urban_data = urban_data[0] # Single band
        
        # Filter out nodata and calculate mean urban LST
        valid_urban_data = urban_data[urban_data != src.nodata]
        urban_lst_avg_k = valid_urban_data.mean()
        
        # 2. Calculate Rural LST (Use the area OUTSIDE the urban polygon)
        
        # Get the entire LST array
        full_lst_array = src.read(1)
        
        # Create a mask for the rural area (invert the urban mask process)
        # Create a mask array of the same shape as the raster
        urban_mask_array = src.read_masks(1) # Read the existing mask/valid data
        
        # Create a boolean mask where True is inside the urban polygon (using a simplified method)
        # This is a simplification; proper inversion is more complex but this works for the mock data
        
        # Find the pixel indices that correspond to the urban area
        row_min, row_max = urban_start, urban_end
        col_min, col_max = urban_start, urban_end
        
        # Create a mask where False is the urban area (set to True by default, False for urban)
        rural_mask = np.ones(full_lst_array.shape, dtype=bool)
        rural_mask[row_min:row_max, col_min:col_max] = False
        
        # Apply the rural mask and filter nodata
        rural_data = full_lst_array[rural_mask]
        valid_rural_data = rural_data[rural_data != src.nodata]
        rural_lst_avg_k = valid_rural_data.mean()
        
    # --- 3. UHI Magnitude Calculation ---
    
    # Convert Kelvin to Celsius for readability
    urban_lst_avg_c = urban_lst_avg_k - 273.15
    rural_lst_avg_c = rural_lst_avg_k - 273.15
    
    # UHI Magnitude
    uhi_magnitude = urban_lst_avg_c - rural_lst_avg_c

    # --- 4. Output Results ---
    print("\n" + "="*40)
    print("Urban Heat Island (UHI) Analysis Results")
    print("="*40)
    print(f"Average Urban LST: {urban_lst_avg_c:.2f} °C")
    print(f"Average Rural LST: {rural_lst_avg_c:.2f} °C")
    print(f"\nUHI Magnitude (ΔT): {uhi_magnitude:.2f} °C")
    print("="*40)
    
    if uhi_magnitude > 2.0:
        print("Conclusion: Significant Urban Heat Island effect detected.")
    else:
        print("Conclusion: UHI effect is minor or negligible.")
        
    # --- 5. Visualization ---
    fig, ax = plt.subplots(1, 1, figsize=(8, 8))
    
    # Plot the full LST array (simulated heatmap)
    im = ax.imshow(full_lst_array - 273.15, cmap='hot', origin='upper', extent=[xmin, xmax, ymin, ymax])
    fig.colorbar(im, ax=ax, label='Land Surface Temperature (°C)')
    
    # Overlay the urban boundary
    urban_gdf.plot(ax=ax, facecolor='none', edgecolor='blue', linewidth=2, label='Urban Boundary')
    
    ax.set_title("Simulated Land Surface Temperature (LST) Map")
    ax.set_xlabel("Easting (m)")
    ax.set_ylabel("Northing (m)")
    
    # Add a marker for the rural average location (e.g., top-left corner)
    ax.plot(1000, 9000, 'go', markersize=10, label=f'Rural Avg: {rural_lst_avg_c:.1f}°C')
    # Add a marker for the urban average location (center)
    ax.plot(xmax/2, ymax/2, 'rx', markersize=10, mew=2, label=f'Urban Avg: {urban_lst_avg_c:.1f}°C')
    
    ax.legend(loc='lower left')
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    # Step 1: Generate necessary geospatial files
    generate_mock_data()
    
    # Step 2: Run the analysis
    analyze_uhi()