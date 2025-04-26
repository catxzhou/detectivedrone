import numpy as np
import math
import datetime
import xml.dom.minidom as minidom


def create_optimized_trajectory(barcode_positions, start_position=None, max_velocity=2.0, battery_capacity=100.0):
    """
    Create an optimized trajectory to visit all barcodes

    Args:
        barcode_positions: Dictionary of barcode positions from triangulation
        start_position: Starting position of the drone (optional)
        max_velocity: Maximum drone velocity in m/s
        battery_capacity: Battery capacity in percentage

    Returns:
        List of waypoints with position, orientation and timing
    """
    # Use pre-calculated drone waypoints from triangulation
    target_waypoints = []
    for palette_id, data in barcode_positions.items():
        barcode_pos = np.array(data['barcode_center'])
        optimal_view_pos = np.array(data['drone_waypoint'])

        # Calculate orientation: drone should face the barcode
        view_direction = barcode_pos - optimal_view_pos
        orientation = calculate_orientation(view_direction)

        target_waypoints.append({
            'position': optimal_view_pos.tolist(),
            'orientation': orientation,
            'palette_id': palette_id,
            'barcode_position': barcode_pos.tolist()
        })

    # Default start position if none provided
    if start_position is None:
        start_position = np.array([0, 0, 2.0])  # Default height of 2m

    # Use improved optimization technique (2-opt) instead of simple nearest neighbor
    optimized_order = optimize_waypoint_order_2opt(start_position, target_waypoints)
    ordered_waypoints = [target_waypoints[i] for i in optimized_order]

    # Generate complete path with direct connections between waypoints
    final_trajectory = generate_complete_path(
        start_position,
        ordered_waypoints,
        max_velocity,
        battery_capacity
    )

    return final_trajectory


def calculate_orientation(direction_vector):
    """
    Calculate orientation angles (roll, pitch, yaw) from a direction vector.

    Args:
        direction_vector: 3D vector pointing in desired direction

    Returns:
        List [roll, pitch, yaw] in radians
    """
    # Normalize direction vector
    if np.linalg.norm(direction_vector) > 0:
        direction = direction_vector / np.linalg.norm(direction_vector)
    else:
        return [0, 0, 0]

    # Calculate yaw (rotation around z-axis)
    yaw = np.arctan2(direction[1], direction[0])

    # Calculate pitch (rotation around y-axis)
    pitch = np.arctan2(-direction[2], np.sqrt(direction[0] ** 2 + direction[1] ** 2))

    # Roll is typically kept at 0 for stable flight
    roll = 0

    return [roll, pitch, yaw]


def optimize_waypoint_order_2opt(start_position, waypoints):
    """
    Use a 2-opt algorithm to solve the TSP problem
    of visiting all waypoints efficiently.

    Args:
        start_position: Starting position as numpy array
        waypoints: List of waypoint dictionaries

    Returns:
        List of indices representing the optimal visiting order
    """
    if not waypoints:
        return []

    # Extract positions into numpy arrays
    positions = [np.array(wp['position']) for wp in waypoints]

    # Initial solution using nearest neighbor
    current_pos = start_position
    unvisited = list(range(len(waypoints)))
    tour = []

    while unvisited:
        # Find nearest unvisited waypoint
        nearest_idx = min(unvisited, key=lambda i: np.linalg.norm(positions[i] - current_pos))
        tour.append(nearest_idx)
        current_pos = positions[nearest_idx]
        unvisited.remove(nearest_idx)

    # Improve with 2-opt swaps
    improved = True
    while improved:
        improved = False
        for i in range(len(tour) - 2):
            for j in range(i + 2, len(tour)):
                # Calculate current distance
                dist_current = (np.linalg.norm(positions[tour[i]] - positions[tour[i + 1]]) +
                                np.linalg.norm(positions[tour[j]] - positions[tour[(j + 1) % len(tour)]]))

                # Calculate distance if we swap
                dist_new = (np.linalg.norm(positions[tour[i]] - positions[tour[j]]) +
                            np.linalg.norm(positions[tour[i + 1]] - positions[tour[(j + 1) % len(tour)]]))

                if dist_new < dist_current:
                    # Reverse the subpath to create 2-opt move
                    tour[i + 1:j + 1] = reversed(tour[i + 1:j + 1])
                    improved = True
                    break
            if improved:
                break

    return tour


def generate_complete_path(start_position, ordered_waypoints, max_velocity=2.0, battery_capacity=100.0):
    """
    Generate a complete path with timing.
    Creates direct paths between waypoints without obstacles.

    Args:
        start_position: Starting drone position
        ordered_waypoints: List of waypoints in visitation order
        max_velocity: Maximum drone velocity
        battery_capacity: Battery capacity in percentage

    Returns:
        Complete list of waypoints including intermediate points with timing
    """
    complete_path = []
    current_pos = np.array(start_position) if isinstance(start_position, list) else start_position
    current_time = 0.0
    battery_remaining = battery_capacity
    battery_drain_rate = 0.1  # % per meter

    # Add starting waypoint
    complete_path.append({
        'position': current_pos.tolist(),
        'orientation': [0, 0, 0],
        'waypoint_type': 'start',
        'time': current_time,
        'battery': battery_remaining
    })

    # For each target waypoint, create direct path with intermediate points
    for wp in ordered_waypoints:
        target_pos = np.array(wp['position']) if isinstance(wp['position'], list) else wp['position']

        # Calculate direct path with intermediate points for smooth movement
        direction = target_pos - current_pos
        distance = np.linalg.norm(direction)

        # Add intermediate points every 2 meters for smoother flight
        if distance > 2.0:
            num_points = max(1, int(distance / 2.0))

            # Generate intermediate waypoints
            for i in range(1, num_points):
                # Calculate position ratio along the path
                ratio = i / num_points
                intermediate_pos = current_pos + direction * ratio

                # Calculate time to reach this point
                segment_distance = distance * (1 / num_points)
                segment_time = segment_distance / max_velocity
                current_time += segment_time

                # Calculate battery consumption
                battery_drain = segment_distance * battery_drain_rate
                battery_remaining -= battery_drain

                # Calculate orientation towards the next point
                intermediate_orientation = calculate_orientation(direction)

                # Add intermediate waypoint
                complete_path.append({
                    'position': intermediate_pos.tolist(),
                    'orientation': intermediate_orientation,
                    'waypoint_type': 'intermediate',
                    'time': current_time,
                    'battery': battery_remaining
                })

        # Add time for final approach
        final_segment_distance = distance / num_points if distance > 2.0 else distance
        current_time += final_segment_distance / max_velocity

        # Add time for barcode scanning operation
        scan_time = 3.0  # seconds to scan barcode
        current_time += scan_time

        # Battery usage for final approach and hovering
        battery_remaining -= final_segment_distance * battery_drain_rate
        battery_remaining -= scan_time * 0.05  # Hovering battery drain

        # Add target waypoint
        complete_path.append({
            'position': wp['position'],
            'orientation': wp['orientation'],
            'palette_id': wp.get('palette_id', 'unknown'),
            'waypoint_type': 'target',
            'time': current_time,
            'battery': battery_remaining,
            'barcode_position': wp['barcode_position']
        })

        # Update current position for next iteration
        current_pos = target_pos

    return complete_path


