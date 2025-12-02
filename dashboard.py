"""
Chesapeake Bay Bridge Eastbound - Vessel Allision Risk Dashboard
Real-time monitoring of vessel traffic and collision risks
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import json
from datetime import datetime
from pathlib import Path

from vessel_analysis import (
    BRIDGE_LAT, BRIDGE_LON, CHESAPEAKE_BAY_BRIDGE_EASTBOUND_PIERS,
    analyze_all_vessels, get_threat_summary, haversine_distance
)

# Page configuration
st.set_page_config(
    page_title="Chesapeake Bay Bridge Eastbound - Vessel Monitor",
    page_icon="🌉",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .threat-critical { color: #ff4444; font-weight: bold; }
    .threat-high { color: #ffaa00; font-weight: bold; }
    .threat-medium { color: #ffff44; }
    .threat-low { color: #44ff44; }
    .metric-card {
        background-color: #1a1a1a;
        padding: 15px;
        border-radius: 10px;
        margin: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Header with logo
col_logo, col_title = st.columns([1, 5])
with col_logo:
    logo_path = Path(__file__).parent / "Logo-Roebling-Labs.webp"
    if logo_path.exists():
        st.image(str(logo_path), width=100)

with col_title:
    st.title("Chesapeake Bay Bridge Eastbound")
    st.subheader("Vessel Allision Risk Monitoring System")


def load_vessel_data():
    """Load vessel data from JSON file"""
    json_path = Path(__file__).parent / "current_ships.json"
    if json_path.exists():
        with open(json_path, 'r') as f:
            data = json.load(f)
            return data.get('vessels', []), data.get('timestamp', 'Unknown')
    return [], None


def get_threat_color(threat_level):
    """Return color based on threat level"""
    colors = {
        'CRITICAL': '#ff4444',
        'HIGH': '#ffaa00',
        'MEDIUM': '#ffff44',
        'LOW': '#44ff44'
    }
    return colors.get(threat_level, '#888888')


def create_map(vessels, analyses):
    """Create Folium map with vessels and piers"""
    # Create map centered on bridge with no default tiles
    m = folium.Map(
        location=[BRIDGE_LAT, BRIDGE_LON],
        zoom_start=11,
        tiles=None
    )

    # Add OpenStreetMap as base layer
    folium.TileLayer(
        tiles='https://tile.openstreetmap.org/{z}/{x}/{y}.png',
        attr='© OpenStreetMap contributors',
        name='OpenStreetMap',
        overlay=False,
        control=True
    ).add_to(m)

    # Add NOAA ENC nautical charts as alternative base layer
    folium.WmsTileLayer(
        url='https://gis.charttools.noaa.gov/arcgis/rest/services/MCS/ENCOnline/MapServer/exts/MaritimeChartService/WMSServer',
        layers='0,1,2,3,4,5,6,7',
        fmt='image/png',
        transparent=True,
        attr='© NOAA',
        name='NOAA Nautical Charts',
        overlay=False,
        control=True
    ).add_to(m)

    # Add OpenSeaMap nautical chart overlay
    folium.TileLayer(
        tiles='https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png',
        attr='© OpenSeaMap contributors',
        name='OpenSeaMap Overlay',
        overlay=True,
        control=True
    ).add_to(m)

    # Add pier markers
    for pier_name, pier_data in CHESAPEAKE_BAY_BRIDGE_EASTBOUND_PIERS.items():
        # Determine if this is a tower or anchorage pier
        if 'Tower' in pier_name:
            icon_color = 'red'
            icon_type = 'tower'
        elif 'Anchorage' in pier_name:
            icon_color = 'orange'
            icon_type = 'anchor'
        else:
            icon_color = 'blue'
            icon_type = 'pier'

        folium.Marker(
            location=[pier_data['lat'], pier_data['lon']],
            popup=f"<b>{pier_name}</b><br>Water Depth: {pier_data['water_depth_ft']} ft",
            tooltip=pier_name,
            icon=folium.Icon(color=icon_color, icon='info-sign')
        ).add_to(m)

    # Create analysis lookup by MMSI
    analysis_lookup = {a['mmsi']: a for a in analyses}

    # Add vessel markers
    for vessel in vessels:
        lat = vessel.get('Latitude')
        lon = vessel.get('Longitude')
        if lat is None or lon is None:
            continue

        mmsi = vessel.get('mmsi', 'N/A')
        analysis = analysis_lookup.get(mmsi, {})
        threat_level = analysis.get('threat_level', 'LOW')
        threat_color = get_threat_color(threat_level)

        name = vessel.get('name', 'Unknown')
        sog = vessel.get('Sog', 0)
        cog = vessel.get('Cog', 0)

        popup_html = f"""
        <div style="width: 200px;">
            <b>{name}</b><br>
            MMSI: {mmsi}<br>
            Speed: {sog:.1f} knots<br>
            Course: {cog:.1f}°<br>
            Threat: <span style="color: {threat_color}; font-weight: bold;">{threat_level}</span><br>
            Closest Pier: {analysis.get('closest_pier', 'N/A')}<br>
            Distance: {analysis.get('distance_nm', 0):.2f} nm
        </div>
        """

        # Use CircleMarker for vessels
        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{name} ({threat_level})",
            color=threat_color,
            fill=True,
            fillColor=threat_color,
            fillOpacity=0.7
        ).add_to(m)

    # Layer control must be added LAST, after all map elements
    folium.LayerControl(position='topleft', collapsed=True).add_to(m)

    return m


# Load data
vessels, timestamp = load_vessel_data()
analyses = analyze_all_vessels(vessels) if vessels else []
summary = get_threat_summary(analyses)

# Display last update time
if timestamp:
    st.info(f"Last data update: {timestamp}")

# Threat Summary
st.header("Threat Summary")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Vessels", summary['total_vessels'])

with col2:
    st.metric("Critical Threats", summary['critical'])

with col3:
    st.metric("High Threats", summary['high'])

with col4:
    st.metric("Medium Threats", summary['medium'])

with col5:
    st.metric("Approaching Vessels", summary['approaching_count'])

# Map
st.header("Live Vessel Map")
if vessels:
    vessel_map = create_map(vessels, analyses)
    st_folium(vessel_map, width=None, height=600)
else:
    st.warning("No vessel data available. Run update_ships.py to fetch current data.")

# Threat Analysis Table
st.header("Vessel Threat Analysis")
if analyses:
    # Filter options
    threat_filter = st.multiselect(
        "Filter by threat level:",
        ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
        default=['CRITICAL', 'HIGH', 'MEDIUM']
    )

    filtered_analyses = [a for a in analyses if a['threat_level'] in threat_filter]

    if filtered_analyses:
        for analysis in filtered_analyses[:20]:  # Show top 20
            threat_color = get_threat_color(analysis['threat_level'])

            with st.expander(
                f"🚢 {analysis['vessel_name']} - {analysis['threat_level']}",
                expanded=analysis['threat_level'] in ['CRITICAL', 'HIGH']
            ):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**MMSI:** {analysis['mmsi']}")
                    st.write(f"**Type:** {analysis['ship_type']}")
                    st.write(f"**Length:** {analysis['length_m'] or 'Unknown'} m")
                    st.write(f"**Est. Mass:** {analysis['mass_tonnes']:,.0f} tonnes")

                with col2:
                    st.write(f"**Speed:** {analysis['speed_knots']:.1f} knots")
                    st.write(f"**Course:** {analysis['course']:.1f}°")
                    st.write(f"**Closest Pier:** {analysis['closest_pier']}")
                    st.write(f"**Distance:** {analysis['distance_nm']:.2f} nm")

                with col3:
                    st.write(f"**Approaching:** {'Yes' if analysis['is_approaching'] else 'No'}")
                    st.write(f"**Time to Pier:** {analysis['time_to_pier_min']:.1f} min" if analysis['time_to_pier_min'] < 1000 else "**Time to Pier:** N/A")
                    st.write(f"**Impact Force:** {analysis['impact_force_MN']:.2f} MN")
                    st.markdown(f"**Threat Score:** <span style='color: {threat_color}; font-weight: bold;'>{analysis['threat_score']}</span>", unsafe_allow_html=True)
    else:
        st.info("No vessels match the selected threat levels.")
else:
    st.info("No vessel analysis data available.")

# Bridge Information
st.header("Bridge Information")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Chesapeake Bay Bridge (Eastbound)")
    st.write("""
    - **Also Known As:** William Preston Lane Jr. Memorial Bridge
    - **Location:** Maryland, connecting Sandy Point (Western Shore) to Kent Island (Eastern Shore)
    - **Opened:** 1952 (Original span), 1973 (Parallel span)
    - **Total Length:** 4.3 miles (6.9 km)
    - **Main Span:** 1,600 feet (488 m)
    - **Clearance:** 186 feet (57 m)
    - **Structure:** Dual-span bridge (Eastbound is the original 1952 span)
    - **Piers Monitored:** 20 piers including 2 main towers and 2 anchorages
    """)

with col2:
    st.subheader("Maritime Navigation")
    st.write("""
    - **Waterway:** Chesapeake Bay
    - **Channel:** Main shipping channel passes between Piers 9 and 10 (Towers)
    - **Traffic:** Major shipping lane for Baltimore Harbor and Chesapeake Bay ports
    - **Vessel Types:** Container ships, tankers, bulk carriers, recreational vessels
    - **Tidal Range:** Approximately 1-2 feet
    - **Current:** Variable, influenced by tidal flow and wind
    """)

# Pier Details
st.header("Pier Locations")
pier_data_display = []
for pier_name, pier_data in CHESAPEAKE_BAY_BRIDGE_EASTBOUND_PIERS.items():
    pier_data_display.append({
        'Pier': pier_name,
        'Latitude': f"{pier_data['lat']:.6f}",
        'Longitude': f"{pier_data['lon']:.6f}",
        'Water Depth (ft)': pier_data['water_depth_ft']
    })

st.dataframe(pier_data_display, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888;'>
        Chesapeake Bay Bridge Eastbound Vessel Allision Risk Monitor | Powered by Roebling Labs<br>
        Data source: AIS vessel transponders via AISStream.io
    </div>
    """,
    unsafe_allow_html=True
)
