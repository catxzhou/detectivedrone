import math

# need to take optimization from flight_optimization

def generate_kml_file(trajectory, origin_lat=0.0, origin_lon=0.0, filename="drone_mission.kml"):
    """
    Generate a KML file from the drone trajectory for visualization in Google Earth.

    Args:
        trajectory: List of waypoints with position and time information
        origin_lat: Latitude of the local origin (0,0,0)
        origin_lon: Longitude of the local origin (0,0,0)
        filename: Output KML filename

    Returns:
        Filename of generated KML file
    """
    # Constants for converting local coordinates to GPS
    earth_radius = 6378137.0  # Earth radius in meters
    meters_per_lat = 111320.0  # Meters per degree latitude (approximate)

    # Create KML document
    doc = minidom.getDOMImplementation().createDocument(None, "kml", None)
    kml = doc.documentElement
    kml.setAttribute("xmlns", "http://www.opengis.net/kml/2.2")

    # Create Document element
    document = doc.createElement("Document")
    kml.appendChild(document)

    # Create name for the document
    name = doc.createElement("name")
    name_text = doc.createTextNode("Drone Mission Path")
    name.appendChild(name_text)
    document.appendChild(name)

    # Create Style for waypoints
    for waypoint_type in ['start', 'intermediate', 'target']:
        style = doc.createElement("Style")
        style.setAttribute("id", f"{waypoint_type}Style")

        icon_style = doc.createElement("IconStyle")
        icon = doc.createElement("Icon")
        href = doc.createElement("href")

        # Different icons for different waypoint types
        if waypoint_type == 'start':
            href_text = doc.createTextNode("http://maps.google.com/mapfiles/kml/shapes/airports.png")
            scale = doc.createElement("scale")
            scale_text = doc.createTextNode("1.2")
            scale.appendChild(scale_text)
            icon_style.appendChild(scale)
        elif waypoint_type == 'target':
            href_text = doc.createTextNode("http://maps.google.com/mapfiles/kml/shapes/target.png")
            scale = doc.createElement("scale")
            scale_text = doc.createTextNode("1.0")
            scale.appendChild(scale_text)
            icon_style.appendChild(scale)
        else:
            href_text = doc.createTextNode("http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png")
            scale = doc.createElement("scale")
            scale_text = doc.createTextNode("0.7")
            scale.appendChild(scale_text)
            icon_style.appendChild(scale)

        href.appendChild(href_text)
        icon.appendChild(href)
        icon_style.appendChild(icon)
        style.appendChild(icon_style)
        document.appendChild(style)

    # Create Style for flight path
    style = doc.createElement("Style")
    style.setAttribute("id", "flightPathStyle")

    line_style = doc.createElement("LineStyle")
    color = doc.createElement("color")
    color_text = doc.createTextNode("ff0000ff")  # Red line
    width = doc.createElement("width")
    width_text = doc.createTextNode("4")

    color.appendChild(color_text)
    width.appendChild(width_text)
    line_style.appendChild(color)
    line_style.appendChild(width)
    style.appendChild(line_style)
    document.appendChild(style)

    # Create Folder for waypoints
    folder_waypoints = doc.createElement("Folder")
    folder_name = doc.createElement("name")
    folder_name_text = doc.createTextNode("Waypoints")
    folder_name.appendChild(folder_name_text)
    folder_waypoints.appendChild(folder_name)
    document.appendChild(folder_waypoints)

    # Create Placemarks for each waypoint
    for i, wp in enumerate(trajectory):
        placemark = doc.createElement("Placemark")

        # Set name
        pm_name = doc.createElement("name")
        waypoint_type = wp.get('waypoint_type', 'unknown')

        if waypoint_type == 'start':
            name_text = f"Start"
        elif waypoint_type == 'target':
            name_text = f"Target {wp.get('palette_id', i)}"
        else:
            name_text = f"Waypoint {i}"

        pm_name_text = doc.createTextNode(name_text)
        pm_name.appendChild(pm_name_text)
        placemark.appendChild(pm_name)

        # Set style
        style_url = doc.createElement("styleUrl")
        style_url_text = doc.createTextNode(f"#{waypoint_type}Style")
        style_url.appendChild(style_url_text)
        placemark.appendChild(style_url)

        # Set description
        description = doc.createElement("description")
        desc_text = f"Time: {wp.get('time', 0):.1f}s<br/>"
        desc_text += f"Battery: {wp.get('battery', 0):.1f}%<br/>"
        if 'orientation' in wp:
            roll, pitch, yaw = wp['orientation']
            desc_text += f"Orientation: Roll={math.degrees(roll):.1f}°, "
            desc_text += f"Pitch={math.degrees(pitch):.1f}°, "
            desc_text += f"Yaw={math.degrees(yaw):.1f}°<br/>"

        description_text = doc.createTextNode(desc_text)
        description.appendChild(description_text)
        placemark.appendChild(description)

        # Set coordinates
        point = doc.createElement("Point")
        coordinates = doc.createElement("coordinates")

        # Convert local XYZ to lat/lon/alt
        x, y, z = wp['position']

        # Simple flat-earth approximation
        lon = origin_lon + (x / (earth_radius * math.cos(math.radians(origin_lat)))) * (180.0 / math.pi)
        lat = origin_lat + (y / meters_per_lat)
        alt = z  # Altitude in meters

        coord_text = doc.createTextNode(f"{lon},{lat},{alt}")
        coordinates.appendChild(coord_text)
        point.appendChild(coordinates)
        placemark.appendChild(point)

        folder_waypoints.appendChild(placemark)

    # Create LineString for the flight path
    placemark = doc.createElement("Placemark")

    # Set name
    pm_name = doc.createElement("name")
    pm_name_text = doc.createTextNode("Flight Path")
    pm_name.appendChild(pm_name_text)
    placemark.appendChild(pm_name)

    # Set style
    style_url = doc.createElement("styleUrl")
    style_url_text = doc.createTextNode("#flightPathStyle")
    style_url.appendChild(style_url_text)
    placemark.appendChild(style_url)

    # Create LineString
    linestring = doc.createElement("LineString")

    # Set altitude mode
    altitude_mode = doc.createElement("altitudeMode")
    altitude_mode_text = doc.createTextNode("absolute")
    altitude_mode.appendChild(altitude_mode_text)
    linestring.appendChild(altitude_mode)

    # Set coordinates
    coordinates = doc.createElement("coordinates")
    coord_text = ""

    for wp in trajectory:
        x, y, z = wp['position']

        # Convert local XYZ to lat/lon/alt
        lon = origin_lon + (x / (earth_radius * math.cos(math.radians(origin_lat)))) * (180.0 / math.pi)
        lat = origin_lat + (y / meters_per_lat)
        alt = z  # Altitude in meters

        coord_text += f"{lon},{lat},{alt} "

    coord_text_node = doc.createTextNode(coord_text)
    coordinates.appendChild(coord_text_node)
    linestring.appendChild(coordinates)
    placemark.appendChild(linestring)

    document.appendChild(placemark)

    # Write the KML file
    with open(filename, "w") as f:
        f.write(doc.toprettyxml(indent="  "))

    return filename

