"""
Drainage Service

Models drainage network capacity and utilization.

Drainage networks consist of:
- Nodes: storm drains, catch basins, pipes with capacity limits
- Edges: connections between nodes
- Blockage: debris, leaves, sediment reducing effective capacity

The service calculates:
- Effective capacity per node (accounting for blockage)
- Total system capacity
- Utilization percentage
- Overloaded nodes
- Excess water that cannot be drained

Assumptions:
- Simplified node-based model without full hydraulic routing
- Blockage uniformly affects node capacity
- No dynamic pipe flow simulation

Real systems would use:
- SWMM (Storm Water Management Model)
- HEC-RAS
- Full 1D/2D hydraulic models
"""

from typing import List, Tuple
from app.models.schemas import DrainageNetwork, DrainageNode, NodeResult
from app.config import FloodConstants
from app.drainage_config import (
    BRIMSTOWAD_HISTORICAL_REFERENCE_RAINFALL_MM_HR,
    DEFAULT_DRAINAGE_BLOCKAGE_FACTOR,
    DEFAULT_DRAINAGE_SILTATION_FACTOR,
    DEFAULT_DRAINAGE_RUNOFF_ADJUSTMENT,
    BRIMSTOWAD_MUMBAI_HIERARCHY,
    BRIMSTOWAD_HISTORICAL_FLOOD_PRONE_LOCATIONS,
)

def calculate_effective_capacity(node: DrainageNode) -> float:
    """Calculate effective capacity accounting for blockage (model assumption)."""
    # Blockage factor is a MODEL ASSUMPTION justified by historical reports
    # of drain choking, garbage, encroachment, structural deficiencies.
    # The PDF does not provide per-node blockage measurements.
    return node.capacity_m3_hr * (1.0 - node.blockage_factor)

def process_drainage(
    drainage: DrainageNetwork,
    inflow_m3_hr: float
) -> Tuple[float, List[NodeResult], List[str]]:
    """
    Process drainage network and determine excess water.

    DISTINCTION NOTE:
    - The 25 mm/hr figure (BRIMSTOWAD) is a historical SYSTEM-LEVEL reference
      for the old SWD at low tide. It is NOT assigned as capacity of every node.
    - Node-level blockage/siltation factors are MODEL ASSUMPTIONS (PDF gives
      no per-node hydraulic data). Blockage factor reflects reported historical
      causes: drain choking, garbage, encroachment, structural deficiency.
    - Synthetic drainage graph remains the prototype (no real GIS network
      from the PDF - the PDF contains no coordinate-level drainage geometry).

    Args:
        drainage: Network definition (prototype synthetic graph; configurable)
        inflow_m3_hr: Total runoff inflow rate

    Returns:
        Tuple of (excess_water_m3_hr, node_results, overloaded_node_ids)
    """
    # Calculate total effective capacity
    total_effective_capacity = 0.0
    node_results = []

    for node in drainage.nodes:
        effective_cap = calculate_effective_capacity(node)
        total_effective_capacity += effective_cap

        # For simplicity, distribute inflow proportionally to capacity
        # In reality, this would be based on hydraulic routing
        if total_effective_capacity > 0:
            node_share = effective_cap / max(1.0, inflow_m3_hr)
        else:
            node_share = 0.0

        node_results.append(NodeResult(
            id=node.id,
            effective_capacity=effective_cap,
            utilization_pct=0.0,  # Will calculate after we know total
            is_overloaded=False
        ))

    # Calculate utilization
    if total_effective_capacity > 0:
        utilization_pct = (inflow_m3_hr / total_effective_capacity) * 100.0
    else:
        utilization_pct = 999.0  # No capacity

    # Update node utilization and detect overloads
    overloaded_nodes = []
    for i, node in enumerate(drainage.nodes):
        node_results[i].utilization_pct = utilization_pct

        if utilization_pct > 100.0:
            node_results[i].is_overloaded = True
            overloaded_nodes.append(node.id)

    # Calculate excess water that cannot be drained
    excess_water_m3_hr = max(0.0, inflow_m3_hr - total_effective_capacity)

    return excess_water_m3_hr, node_results, overloaded_nodes
