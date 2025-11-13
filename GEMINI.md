# ATXCOVER Project Overview

This document provides an overview of the ATXCOVER project, intended to serve as instructional context for future interactions.

## Project Summary

**ATXCOVER** is a comprehensive suite of Python-based tools designed for the synthesis, analysis, and design of microwave and RF systems. It integrates various modules to facilitate the development and management of RF components and systems, providing engineers with a robust platform for their projects.

### Key Features:
*   **Antenna Design and Analysis**: Tools for designing and simulating various antenna configurations.
*   **RF Component Simulation**: Modules for simulating RF components such as filters, amplifiers, and mixers.
*   **Signal Processing Utilities**: Functions for analyzing and processing RF signals.
*   **Data Visualization**: Interactive charts and graphs for visualizing simulation results.
*   **SNMP Management**: Integration with SNMP for monitoring and managing networked RF devices.
*   **Coverage Planner**: Dual-overlay (dBµV/m & dBm) map with ITU-R P.452 loss breakdown, tilt-aware antenna gains and receiver management.
*   **Automatic Context Data**: TX municipality/elevation discovery (SRTM + reverse geocoding) and climate snapshots agregated from the last 360 days via Open-Meteo.
*   **Professional UX**: Sticky navigation, polished control panel, live spinners and climate/location warnings to highlight pending updates.
*   **Azimute Inteligente**: Ajuste fino do rumo da antena com feedback instantâneo (linha pontilhada orientada e normalização automática 0-359°).

### Technologies Used:
*   **Backend**: Python, Flask, Flask-SQLAlchemy, Flask-Migrate, Gunicorn.
*   **Database**: PostgreSQL (implied by `psycopg2-binary` in `requirements.txt`).
*   **Scientific/RF Libraries**: NumPy, SciPy, Matplotlib, Pillow, Astropy, Pycraf, Pyproj, Rasterio, Shapely, Geopy, Geojson, Scikit-learn, ReportLab.
*   **Other**: Alembic for database migrations, `python-dotenv` for environment variables.

## Building and Running the Application

### Local Development

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Gecesars/ATXCOVER.git
    cd ATXCOVER
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the application:**
    ```bash
    python app3.py
    ```
    The application will typically be accessible at `http://localhost:8000` (as configured in `app3.py`).

### Docker Deployment

To run the application in a Docker container:

1.  **Build the Docker image:**
    ```bash
    docker build -t atxcover .
    ```
2.  **Run the Docker container:**
    ```bash
    docker run -p 5000:5000 atxcover
    ```
    The application will be accessible at `http://localhost:5000`.

### Cloud Deployment (e.g., Google App Engine, Heroku)

The project is configured for cloud deployment using Gunicorn as the web server.
*   **Google App Engine**: Uses `app.yaml` with `entrypoint: gunicorn -b :8080 app:app`.
*   **Heroku (or similar)**: Uses `Procfile` with `web: gunicorn app:app`.

The entry point `app:app` implies that the main application object named `app` is exposed by a module named `app` (e.g., `app.py`). In the current structure, `app3.py` serves this role locally.

## Development Conventions

*   **Database Migrations**: The project uses Alembic (`migrations/` directory) for managing database schema changes.
*   **Application Structure**: The core application logic resides in `app_core/`, with routes defined in `app_core/routes/`. Templates are in `templates/` and static assets in `static/`.
*   **Environment Variables**: `app3.py` sets `OMP_NUM_THREADS` and `OPENBLAS_NUM_THREADS` environment variables, which are important for controlling the threading behavior of scientific libraries.
