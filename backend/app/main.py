from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health
from app.api import flood, routing, osm_routing, dem

app = FastAPI(
    title="SURAKSHA API",
    description="Urban Flood Nowcasting & Drainage Intelligence System",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(flood.router, prefix="/api/flood", tags=["Flood Prediction"])
app.include_router(routing.router, prefix="/api/routing", tags=["Safe Routing (Demo)"])
app.include_router(osm_routing.router, prefix="/api/osm", tags=["Safe Routing (OSM)"])
app.include_router(dem.router, tags=["DEM & Terrain"])
