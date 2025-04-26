import numpy as np
import json
import cv2

# Camera intrinsics (given/fixed)
K = np.array([
    [2804.051, 0, 2010.41],
    [0, 2804.051, 1512.734],
    [0, 0, 1]
])

# --- Helper Functions ---

def gps_to_local_xy(lat, lon, origin_lat, origin_lon):
    """ Convert GPS to local meters (simple flat-earth approximation) """
    meters_per_deg_lat = 111_320
    meters_per_deg_lon = 40075000 * np.cos(np.radians(origin_lat)) / 360
    dx = (lon - origin_lon) * meters_per_deg_lon
    dy = (lat - origin_lat) * meters_per_deg_lat
    return dx, dy

def extract_bbox_center(bbox):
    """ Calculate center of bounding box in pixel coordinates """
    center_x = bbox['pallet_left'] + bbox['pallet_width'] / 2
    center_y = bbox['pallet_top'] + bbox['pallet_height'] / 2
    return np.array([center_x, center_y])

def build_pose(x, y, z):
    """ Build 4x4 pose matrix (identity rotation assumed) """
    pose = np.eye(4)
    pose[:3, 3] = [x, y, z]
    return pose

def triangulate(K, pose1, pose2, pts1, pts2):
    """ Triangulate corresponding points between two views """
    P1 = K @ pose1[:3, :4]
    P2 = K @ pose2[:3, :4]
    pts4d = cv2.triangulatePoints(P1, P2, pts1.T, pts2.T)
    pts3d = (pts4d / pts4d[3])[:3].T
    return pts3d

def fit_plane(points):
    """ Fit a plane to 3D points, return (normal vector, centroid) """
    centroid = np.mean(points, axis=0)
    centered = points - centroid
    _, _, vh = np.linalg.svd(centered)
    normal = vh[-1]
    return normal, centroid

# --- Main Function ---

def compute_barcode_positions(meta1, meta2, bboxes1, bboxes2):
    """ Main function to compute 3D barcode locations and drone waypoints """

    # Use first image as GPS origin
    origin_lat, origin_lon = meta1['latitude'], meta1['longitude']

    # Build drone poses
    x1, y1 = gps_to_local_xy(meta1['latitude'], meta1['longitude'], origin_lat, origin_lon)
    z1 = meta1.get('altitude', 0)
    pose1 = build_pose(x1, y1, z1)

    x2, y2 = gps_to_local_xy(meta2['latitude'], meta2['longitude'], origin_lat, origin_lon)
    z2 = meta2.get('altitude', 0)
    pose2 = build_pose(x2, y2, z2)

    # Match pallets by pallet_index
    index_to_bbox2 = {bbox['pallet_index']: bbox for bbox in bboxes2}

    matched_pts1 = []
    matched_pts2 = []
    pallet_indices = []

    for bbox1 in bboxes1:
        idx = bbox1['pallet_index']
        if idx in index_to_bbox2:
            bbox2 = index_to_bbox2[idx]
            center1 = extract_bbox_center(bbox1)
            center2 = extract_bbox_center(bbox2)
            matched_pts1.append(center1)
            matched_pts2.append(center2)
            pallet_indices.append(idx)

    matched_pts1 = np.array(matched_pts1)
    matched_pts2 = np.array(matched_pts2)

    # Triangulate points
    points_3d = triangulate(K, pose1, pose2, matched_pts1, matched_pts2)

    # Fit plane to points
    normal, centroid = fit_plane(points_3d)

    # Compute waypoints by offsetting outward
    offset = 2.0  # meters
    waypoints = points_3d + offset * normal

    # Build output
    results = {}
    for idx, pallet_idx in enumerate(pallet_indices):
        results[f'pallet_{pallet_idx}'] = {
            "barcode_center": points_3d[idx].tolist(),
            "drone_waypoint": waypoints[idx].tolist()
        }

    return results

# # --- Example Usage ---
#
# # Example metadata and bounding boxes
# meta1 = {
#     "latitude": 49.09941222,
#     "longitude": 12.180985,
#     "altitude": 10.0
# }
# meta2 = {
#     "latitude": 49.09942222,
#     "longitude": 12.181085,
#     "altitude": 10.0
# }
#
# bboxes1 = [
#     {"pallet_index": 0, "pallet_left": 3771, "pallet_top": 2608, "pallet_width": 258, "pallet_height": 275, "sheet_detected": None}
# ]
# bboxes2 = [
#     {"pallet_index": 0, "pallet_left": 3800, "pallet_top": 2620, "pallet_width": 260, "pallet_height": 270, "sheet_detected": None}
# ]
#
# # Run
# output = compute_barcode_positions(meta1, meta2, bboxes1, bboxes2)
#
# # Save to JSON
# with open('barcode_positions.json', 'w') as f:
#     json.dump(output, f, indent=4)
#
# # Print
# print(json.dumps(output, indent=4))
