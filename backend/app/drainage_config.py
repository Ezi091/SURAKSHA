"""
Drainage Configuration — calibrated from BRIMSTOWAD (1993) historical report.
SOURCE DISTINCTION: OBSERVED/HISTORICAL vs MODEL ASSUMPTIONS.
"""
BRIMSTOWAD_HISTORICAL_REFERENCE_RAINFALL_MM_HR = 25.0
DEFAULT_DRAINAGE_BLOCKAGE_FACTOR = 0.15
DEFAULT_DRAINAGE_SILTATION_FACTOR = 0.10
DEFAULT_DRAINAGE_RUNOFF_ADJUSTMENT = 1.05
BRIMSTOWAD_MUMBAI_HIERARCHY = {
    "major_nallah_width_gt_1_5m_km": 200, "minor_nallah_width_lt_1_5m_km": 87,
    "arch_box_drains_km": 151, "roadside_open_drains_km": 1987,
    "closed_pipe_dhapa_drains_km": 565, "total_swd_length_km": 2991,
    "outfalls": 186, "water_entrances": 30208,
}
BRIMSTOWAD_HISTORICAL_FLOOD_PRONE_LOCATIONS = [
    {"name":"Carnac Bunder","region":"Island City","eliminated":False},
    {"name":"Sandhurst Road Station Area (Low Level)","region":"Island City","eliminated":False},
    {"name":"Sleater Road, Nana Chowk, Grant Road (W)","region":"Island City","eliminated":False},
    {"name":"Maratha Mandir, Mumbai Central","region":"Island City","eliminated":True,"note":"Partially eliminated"},
    {"name":"Satrasta, Mahalaxmi (E)","region":"Island City","eliminated":False},
    {"name":"Sakhubai Mohite Marg, Curry Road","region":"Island City","eliminated":False},
    {"name":"Hindmata Cinema, Dr. B.A. Road, Parel","region":"Island City","eliminated":False},
    {"name":"Dadar T.T.","region":"Island City","eliminated":False},
    {"name":"Gandhi Market, King Circle","region":"Island City","eliminated":True,"note":"Eliminated"},
    {"name":"Rafi Ahmed Kidwai Marg, Shivdi, Wadala","region":"Island City","eliminated":True,"note":"Eliminated"},
    {"name":"Gazdarbund, Santacruz (W)","region":"Western Suburbs","eliminated":False},
    {"name":"Milan Subway, Santacruz (W)","region":"Western Suburbs","eliminated":False},
    {"name":"Malad Subway, Nutan Vidya Mandir, Malad","region":"Western Suburbs","eliminated":False},
    {"name":"Valnai Joglekar Nalla Area in R/South Ward","region":"Western Suburbs","eliminated":False},
    {"name":"Indira Steel Yard, Mulund (W)","region":"Eastern Suburbs","eliminated":True,"note":"Eliminated"},
    {"name":"Damodar Park, L.B.S. Marg, Ghatkopar (W)","region":"Eastern Suburbs","eliminated":False},
    {"name":"Postal Colony, Chembur","region":"Eastern Suburbs","eliminated":True,"note":"Eliminated"},
    {"name":"Umarshi Bappa Chowk, Hemu Kalani Marg, Chembur","region":"Eastern Suburbs","eliminated":False},
    {"name":"Brahmanwadi, Kurla (W)","region":"Eastern Suburbs","eliminated":False},
]
