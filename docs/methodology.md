##  Features

* **Raster Processing:** Utilizes `rasterio` and `numpy` to handle and process LST raster data.
* **Vector/Raster Interaction:** Reads city boundaries (GeoJSON) and calculates average LST within the urban area.
* **Heat Island Identification:** Calculates the UHI magnitude (difference between urban LST and surrounding rural/reference LST).
* **Visualization:** Generates a basic output image (heatmap simulation) using `matplotlib`.

##  Tech Stack

* **Python**
* **Rasterio** (Geospatial raster operations)
* **GeoPandas** (Geospatial vector operations)
* **NumPy** (Numerical arrays)
* **Matplotlib** (Visualization)

##  Installation


1.  **Install dependencies:**
    ```bash
    # Geo-libraries can be complex; ensure a clean environment.
    pip install -r requirements.txt
    ```

3.  **Run the analysis:**
    ```bash
    python analyze_uhi.py
    ```

## Usage

1.  The `analyze_uhi.py` script first generates mock geospatial data (`mock_lst.tif` and `city_boundaries.geojson`).
2.  It then calculates:
    * Average LST for the mock rural area.
    * Average LST for the mock urban area.
    * The UHI magnitude (Urban LST - Rural LST).
3.  The results are printed to the console.
4.  A map visualization of the simulated LST data will be displayed (using Matplotlib).

