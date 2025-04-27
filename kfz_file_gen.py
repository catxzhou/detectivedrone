import math

# optimize_waypoint_order_2opt(), and generate_complete_path()

def generate_kml_waypoints(trajectory, origin_lat, origin_lon, origin_alt):
    """
    Generate KML waypoint entries from trajectory data.

    Args:
        trajectory: List of waypoints from create_optimized_trajectory
        origin_lat: Origin latitude in decimal degrees
        origin_lon: Origin longitude in decimal degrees
        origin_alt: Origin altitude in meters (ellipsoidal height)

    Returns:
        List of KML waypoint XML strings in the required format
    """
    # Constants for converting local coordinates to GPS
    earth_radius = 6378137.0  # Earth radius in meters
    meters_per_lat = 111320.0  # Meters per degree latitude (approximate)

    waypoint_xml_list = []

    for wp in trajectory:
        # Extract position
        x, y, z = wp['position']

        # Convert local XYZ to lat/lon/alt
        lon = origin_lon + (x / (earth_radius * math.cos(math.radians(origin_lat)))) * (180.0 / math.pi)
        lat = origin_lat + (y / meters_per_lat)

        # Calculate height above ground and ellipsoidal height
        ellipsoidal_height = origin_alt + z
        height = z  # Height above ground level

        # Create waypoint XML structure
        xml_string = f'''<Placemark>
  <Point>
    <coordinates>
      {lon:.9f},{lat:.9f}
    </coordinates>
  </Point>
  <wpml:index>{wp.get('index', 0)}</wpml:index>
  <wpml:ellipsoidHeight>{ellipsoidal_height:.9f}</wpml:ellipsoidHeight>
  <wpml:height>{height:.1f}</wpml:height>
</Placemark>'''

        waypoint_xml_list.append(xml_string)

    return waypoint_xml_list


def insert_waypoints_in_kml(input_kml_path, output_kml_path, waypoint_xml_strings):
    """
    Insert generated waypoints into an existing KML file

    Args:
        input_kml_path: Path to the input KML file
        output_kml_path: Path where the modified KML will be saved
        waypoint_xml_strings: List of waypoint XML strings

    Returns:
        Path to the modified KML file
    """
    # Read the input KML file
    with open(input_kml_path, 'r') as f:
        kml_content = f.read()

    # Find the insertion point - this depends on the structure of your KML file
    insertion_marker = "</Document>"  # Adjust based on your file structure

    # Split the content at the insertion point
    if insertion_marker in kml_content:
        pre_insertion, post_insertion = kml_content.split(insertion_marker, 1)

        # Insert waypoints
        waypoints_content = "\n  <!-- Drone Trajectory Waypoints -->\n"
        for wp_xml in waypoint_xml_strings:
            waypoints_content += "  " + wp_xml.replace("\n", "\n  ") + "\n"

        # Combine everything
        new_kml_content = pre_insertion + waypoints_content + insertion_marker + post_insertion

        # Write the modified content to the output file
        with open(output_kml_path, 'w') as f:
            f.write(new_kml_content)

        return output_kml_path
    else:
        raise ValueError(f"Insertion marker '{insertion_marker}' not found in KML file")


# Example usage showing the logical flow of the code
def plan_drone_mission(barcode_positions, start_position, kml_template_path,
                       origin_lat, origin_lon, origin_alt):
    """
    Plan a drone mission and create a KML file with waypoints

    Args:
        barcode_positions: Dictionary of barcode positions from triangulation
        start_position: Starting drone position [x, y, z]
        kml_template_path: Path to KML template file
        origin_lat, origin_lon, origin_alt: GPS coordinates of local origin

    Returns:
        Path to output KML file
    """
    # Step 1: Create optimized trajectory
    trajectory = create_optimized_trajectory(barcode_positions, start_position)

    # Step 2: Generate KML waypoint entries
    waypoint_xml_strings = generate_kml_waypoints(trajectory, origin_lat, origin_lon, origin_alt)

    # Step 3: Insert waypoints into existing KML file
    output_kml_path = kml_template_path.replace('.kml', '_mission.kml')
    result_file = insert_waypoints_in_kml(kml_template_path, output_kml_path, waypoint_xml_strings)

    return result_file
