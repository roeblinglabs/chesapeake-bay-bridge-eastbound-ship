"""
Chesapeake Bay Bridge Eastbound - Vessel Allision Analysis Module
Analyzes vessel traffic and collision risks for the Chesapeake Bay Bridge (Eastbound span)
"""

import math
from datetime import datetime

# Chesapeake Bay Bridge Eastbound coordinates
BRIDGE_LAT = 38.99334868251498
BRIDGE_LON = -76.38219400260512

# Pier locations for the Chesapeake Bay Bridge Eastbound
CHESAPEAKE_BAY_BRIDGE_EASTBOUND_PIERS = {
    'Pier 1': {
        'lat': 39.006685786202446,
        'lon': -76.4030718781911,
        'water_depth_ft': 25
    },
    'Pier 2': {
        'lat': 39.0047100341694,
        'lon': -76.40187242168875,
        'water_depth_ft': 30
    },
    'Pier 3': {
        'lat': 39.000576682498846,
        'lon': -76.39931260304236,
        'water_depth_ft': 35
    },
    'Pier 4': {
        'lat': 38.99934618768639,
        'lon': -76.3984344824108,
        'water_depth_ft': 40
    },
    'Pier 5': {
        'lat': 38.996661450758054,
        'lon': -76.39490712081833,
        'water_depth_ft': 45
    },
    'Pier 6': {
        'lat': 38.99589831874505,
        'lon': -76.39300195801506,
        'water_depth_ft': 50
    },
    'Pier 7 (Anchorage)': {
        'lat': 38.994722737169305,
        'lon': -76.38834446411663,
        'water_depth_ft': 55
    },
    'Pier 8': {
        'lat': 38.994486462598395,
        'lon': -76.38712588978133,
        'water_depth_ft': 60
    },
    'Pier 9 (Tower)': {
        'lat': 38.993873926517374,
        'lon': -76.38489943454631,
        'water_depth_ft': 100
    },
    'Pier 10 (Tower)': {
        'lat': 38.99258665186238,
        'lon': -76.37951868887593,
        'water_depth_ft': 100
    },
    'Pier 11': {
        'lat': 38.992082059562,
        'lon': -76.37728342385851,
        'water_depth_ft': 60
    },
    'Pier 12 (Anchorage)': {
        'lat': 38.99169243968722,
        'lon': -76.3757818114165,
        'water_depth_ft': 55
    },
    'Pier 13': {
        'lat': 38.991308218724654,
        'lon': -76.37390965718366,
        'water_depth_ft': 50
    },
    'Pier 14': {
        'lat': 38.990858413902934,
        'lon': -76.3718974636084,
        'water_depth_ft': 45
    },
    'Pier 15': {
        'lat': 38.990462929792685,
        'lon': -76.37027880005854,
        'water_depth_ft': 40
    },
    'Pier 16': {
        'lat': 38.99001516265438,
        'lon': -76.36827088727092,
        'water_depth_ft': 35
    },
    'Pier 17': {
        'lat': 38.989649864735526,
        'lon': -76.36661155933896,
        'water_depth_ft': 30
    },
    'Pier 18': {
        'lat': 38.988335645418,
        'lon': -76.36151863357634,
        'water_depth_ft': 25
    },
    'Pier 19': {
        'lat': 38.98694086994944,
        'lon': -76.35556555408714,
        'water_depth_ft': 20
    },
    'Pier 20': {
        'lat': 38.98465161655931,
        'lon': -76.34570149047524,
        'water_depth_ft': 15
    }
}


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in nautical miles"""
    R = 3440.065  # Earth's radius in nautical miles

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculate bearing from point 1 to point 2"""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)

    bearing = math.atan2(x, y)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360

    return bearing


def estimate_vessel_mass(ship_type, length_m):
    """Estimate vessel displacement in metric tons based on type and length"""
    if length_m is None or length_m <= 0:
        length_m = 50  # Default assumption

    ship_type_lower = str(ship_type).lower() if ship_type else ''

    # Mass estimation based on vessel type and length
    if 'tanker' in ship_type_lower or 'crude' in ship_type_lower:
        return 0.5 * length_m ** 2.5
    elif 'container' in ship_type_lower or 'cargo' in ship_type_lower:
        return 0.4 * length_m ** 2.4
    elif 'bulk' in ship_type_lower:
        return 0.45 * length_m ** 2.45
    elif 'passenger' in ship_type_lower or 'cruise' in ship_type_lower:
        return 0.25 * length_m ** 2.3
    elif 'tug' in ship_type_lower:
        return 0.6 * length_m ** 2.2
    elif 'fishing' in ship_type_lower:
        return 0.3 * length_m ** 2.1
    else:
        return 0.35 * length_m ** 2.3


def calculate_aashto_impact_force(vessel_mass_tonnes, velocity_knots):
    """
    Calculate vessel impact force using AASHTO methodology
    Returns force in MN (meganewtons)
    """
    # Convert units
    mass_kg = vessel_mass_tonnes * 1000
    velocity_ms = velocity_knots * 0.5144  # knots to m/s

    # Kinetic energy
    KE = 0.5 * mass_kg * velocity_ms ** 2

    # AASHTO impact force estimation (simplified)
    # Based on deformation energy absorption
    deformation_distance = 1.5  # meters (assumed crush depth)
    impact_force = KE / deformation_distance

    # Convert to MN
    impact_force_MN = impact_force / 1e6

    return impact_force_MN


def get_vessel_length(dimension_data):
    """Extract vessel length from AIS dimension data"""
    if isinstance(dimension_data, dict):
        a = dimension_data.get('A', 0) or 0
        b = dimension_data.get('B', 0) or 0
        length = a + b
        if length > 0:
            return length
    return None


def analyze_vessel_threat(vessel, piers=None):
    """
    Analyze threat level of a vessel to bridge piers
    Returns threat analysis dict
    """
    if piers is None:
        piers = CHESAPEAKE_BAY_BRIDGE_EASTBOUND_PIERS

    lat = vessel.get('Latitude')
    lon = vessel.get('Longitude')
    sog = vessel.get('Sog', 0) or 0
    cog = vessel.get('Cog', 0) or 0
    ship_type = vessel.get('ShipType', 'Unknown')
    dimension = vessel.get('Dimension', {})

    if lat is None or lon is None:
        return None

    # Get vessel length and estimate mass
    length_m = get_vessel_length(dimension)
    mass_tonnes = estimate_vessel_mass(ship_type, length_m)

    # Find closest pier
    min_distance = float('inf')
    closest_pier = None

    for pier_name, pier_data in piers.items():
        dist = haversine_distance(lat, lon, pier_data['lat'], pier_data['lon'])
        if dist < min_distance:
            min_distance = dist
            closest_pier = pier_name

    # Calculate bearing to closest pier
    pier_data = piers[closest_pier]
    bearing_to_pier = calculate_bearing(lat, lon, pier_data['lat'], pier_data['lon'])

    # Check if vessel is heading toward pier (within 30 degrees)
    bearing_diff = abs(cog - bearing_to_pier)
    if bearing_diff > 180:
        bearing_diff = 360 - bearing_diff

    is_approaching = bearing_diff < 30

    # Calculate potential impact force
    impact_force = calculate_aashto_impact_force(mass_tonnes, sog)

    # Time to closest point (simplified)
    if sog > 0:
        time_to_pier_hours = min_distance / sog
        time_to_pier_minutes = time_to_pier_hours * 60
    else:
        time_to_pier_minutes = float('inf')

    # Threat level assessment
    threat_level = 'LOW'
    threat_score = 0

    # Distance factor
    if min_distance < 0.5:  # Less than 0.5 nm
        threat_score += 40
    elif min_distance < 1.0:
        threat_score += 25
    elif min_distance < 2.0:
        threat_score += 10

    # Speed factor
    if sog > 12:
        threat_score += 30
    elif sog > 8:
        threat_score += 20
    elif sog > 4:
        threat_score += 10

    # Heading factor
    if is_approaching:
        threat_score += 20

    # Mass/size factor
    if mass_tonnes > 50000:
        threat_score += 10
    elif mass_tonnes > 10000:
        threat_score += 5

    if threat_score >= 60:
        threat_level = 'CRITICAL'
    elif threat_score >= 40:
        threat_level = 'HIGH'
    elif threat_score >= 20:
        threat_level = 'MEDIUM'

    return {
        'vessel_name': vessel.get('name', 'Unknown'),
        'mmsi': vessel.get('mmsi', 'N/A'),
        'ship_type': ship_type,
        'length_m': length_m,
        'mass_tonnes': mass_tonnes,
        'speed_knots': sog,
        'course': cog,
        'closest_pier': closest_pier,
        'distance_nm': min_distance,
        'bearing_to_pier': bearing_to_pier,
        'is_approaching': is_approaching,
        'time_to_pier_min': time_to_pier_minutes,
        'impact_force_MN': impact_force,
        'threat_level': threat_level,
        'threat_score': threat_score
    }


def analyze_all_vessels(vessels_data):
    """Analyze all vessels and return sorted by threat level"""
    analyses = []

    for vessel in vessels_data:
        analysis = analyze_vessel_threat(vessel)
        if analysis:
            analyses.append(analysis)

    # Sort by threat score (highest first)
    analyses.sort(key=lambda x: x['threat_score'], reverse=True)

    return analyses


def get_threat_summary(analyses):
    """Generate summary statistics of vessel threats"""
    if not analyses:
        return {
            'total_vessels': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'approaching_count': 0,
            'max_impact_force': 0
        }

    critical = sum(1 for a in analyses if a['threat_level'] == 'CRITICAL')
    high = sum(1 for a in analyses if a['threat_level'] == 'HIGH')
    medium = sum(1 for a in analyses if a['threat_level'] == 'MEDIUM')
    low = sum(1 for a in analyses if a['threat_level'] == 'LOW')
    approaching = sum(1 for a in analyses if a['is_approaching'])
    max_force = max(a['impact_force_MN'] for a in analyses)

    return {
        'total_vessels': len(analyses),
        'critical': critical,
        'high': high,
        'medium': medium,
        'low': low,
        'approaching_count': approaching,
        'max_impact_force': max_force
    }
