
# SURAKSHA 🌊


## 🏗️ Project Structure

```
SURAKSHA/
├── backend/                    # Python FastAPI server
│   ├── app/
│   │   ├── main.py            # FastAPI app with CORS
│   │   ├── api/
│   │   │   └── flood.py       # POST /flood/predict endpoint
│   │   ├── routers/
│   │   │   └── health.py      # GET /health endpoint
│   │   ├── services/          # Physics calculations
│   │   │   ├── runoff_service.py
│   │   │   ├── terrain_service.py
│   │   │   ├── drainage_service.py
│   │   │   └── flood_service.py
│   │   ├── models/
│   │   │   └── schemas.py     # Pydantic models
│   │   └── config.py          # Constants & risk levels
│   ├── tests/
│   │   └── test_flood_engine.py
│   ├── requirements.txt
│   └── venv/
│
├── frontend/                   # React + Vite dashboard
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/
│   │   │   └── floodApi.js    # API client (ready for Phase 3)
│   │   └── data/
│   │       └── mockData.js    # Mock data
│   ├── package.json
│   └── vite.config.js
│
├── data/
│   ├── rainfall/              # Rainfall data (Phase 3+)
│   ├── terrain/               # DEM/elevation (Phase 3+)
│   ├── drainage/              # Drainage network (Phase 3+)
│   ├── roads/                 # Road data (Phase 3+)
│   └── boundaries/            # Zone boundaries (Phase 3+)
│
├── WHAT_CAN_IT_DO.md          # Simple overview
├── QUICKSTART.md              # How to use
├── CURRENT_CAPABILITIES.md    # Detailed features
└── README.md                  # This file
```

