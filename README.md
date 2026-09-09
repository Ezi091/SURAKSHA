# SURAKSHA

**Urban Flood Nowcasting & Safe Routing System**

SURAKSHA is a software-based urban flood prediction system designed for flood-prone areas of Mumbai. It combines rainfall, terrain, drainage conditions, and road-network data to estimate flood risk and water depth for the next 0–3 hours.

## Features
- Rainfall-based flood prediction
- DEM-based terrain and low-point analysis
- Drainage capacity and runoff modeling
- Flood risk and water-depth estimation
- Interactive GIS dashboard
- OSM-based safe route planning

## Tech Stack
- **Frontend:** React, Vite, Leaflet
- **Backend:** Python, FastAPI
- **Data:** IMD rainfall, OpenTopography DEM, OpenStreetMap, BRIMSTOWAD/BMC data
- **Testing:** Pytest

## Run the Project

### Backend
```bash
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --port 800
