import numpy as np
import json
import cv2
from detect_pallets_barcodes import main as bbox_pallet_barcode

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
pallets_detection = bbox_pallet_barcode()

def compute_barcode_positions(pallets_detection):

    barcode_positions = []

    for image_name, pallets in pallets_detection.items():
        for pallet in pallets:
            sheet = pallet.get('sheet_detected')
            if sheet is not None:
                # Compute barcode center
                center_x = sheet['sheet_left'] + sheet['sheet_width'] / 2
                center_y = sheet['sheet_top'] + sheet['sheet_height'] / 2

                barcode_info = {
                    'image_name': image_name,
                    'pallet_index': pallet['pallet_index'],
                    'barcode_center_x': center_x,
                    'barcode_center_y': center_y
                }

                barcode_positions.append(barcode_info)

    return barcode_positions

barcode_positions = compute_barcode_positions(pallets_detection)

def triangulate_barcodes(barcode_positions, metadata_per_image):
    barcode_world_positions = []

    for barcode in barcode_positions:
        image_name = barcode['image_name']
        center_x = barcode['barcode_center_x']
        center_y = barcode['barcode_center_y']

        metadata = metadata_per_image.get(image_name)
        if metadata is None:
            print(f"No metadata for {image_name}, skipping...")
            continue

        focal_length = metadata['focal_length']  # in mm
        latitude = metadata['latitude']
        longitude = metadata['longitude']
        altitude = metadata['altitude']  # you might need this!

        # Example: normalize pixel to optical center (you might need calibration)
        # Assume principal point is at image center, and pixel size known
        optical_center_x = metadata['image_width'] / 2
        optical_center_y = metadata['image_height'] / 2

        normalized_x = (center_x - optical_center_x) / focal_length
        normalized_y = (center_y - optical_center_y) / focal_length

        # For a rough triangulation:
        # Assume drone is facing straight down (nadir view),
        # and we approximate 3D X,Y shift based on altitude and normalized image coordinates.

        real_world_x = longitude + normalized_x * altitude  # Simplified
        real_world_y = latitude + normalized_y * altitude
        real_world_z = altitude

        barcode_world_positions.append({
            'pallet_index': barcode['pallet_index'],
            'barcode_world_x': real_world_x,
            'barcode_world_y': real_world_y,
            'barcode_world_z': real_world_z,
        })

    return barcode_world_positions

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
