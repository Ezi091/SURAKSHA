# SURAKSHA Backend - Physics-Inspired Flood Engine MVP

## Overview
This API runs a deterministic, explainable, modular physics-inspired flood prediction pipeline. It is intentionally simplified for the hackathon context to provide responsive end-to-end functionality before integrating full hydrodynamic models.

## Pipeline Architecture
1. **Rainfall & Runoff**: Uses a modified Rational Method (`Q = C * i * A`) where rainfall intensity and area produce a steady runoff volume based on a configurable runoff coefficient representing urban imperviousness.
2. **Terrain Influence**: Uses a simplified terrain accumulation factor driven by average slope and low-point (depression) weights. Shallower slopes increase the accumulation factor. 
3. **Drainage Capacity**: Models municipal drainage as a network of nodes with maximum volumetric extraction capacities (`m³/hr`). Supports a `blockage_factor` to simulate choked drains (e.g., leaves, silt). Distributes runoff against operational capacity to find the system utilization.
4. **Water Depth Estimation**: Excess water that cannot be drained becomes surface accumulation. This volume is spread across the affected area and modified by the terrain factor to simulate local pooling, resulting in a continuous `predicted_water_depth_cm`.
5. **Risk Classification**: Automatically groups continuous depth predictions into distinct ordinal risk levels (e.g., `LOW`, `MODERATE`, `HIGH`, `SEVERE`) using configurable thresholds.

## Predictions Over Time 
The engine accepts arrays of sequential forecasts (e.g. `[T+0, T+1, T+2]`). Excess water from earlier periods carries forward to simulate evolving storm impacts over time.

## Assumptions & Limitations
- This is a *proto-model* and **NOT** a calibrated operational hydrodynamic solver (like SWMM or Mike Urban).
- Surface runoff is treated as steady-state within hour blocks.
- Real 2D routing, pipe-network pressure, surcharge loops, and soil moisture abstractions are bypassed for speed and simplicity.

## Testing
Run the automated test suite using `pytest`. The tests verify fundamental physical relationships (higher rain = more runoff; reduced drainage capacity = higher depth).
