import numpy as np
import cv2
import json

# Camera intrinsics (from you)
K = np.array([
    [2804.051, 0, 2010.41],
    [0, 2804.051, 1512.734],
    [0, 0, 1]
])

# Distortion coefficients
dist_coeffs = np.array([0.116413456, -0.202624237, 0.136982457, 0.000004293, -0.000216595])

# Example camera poses (from metadata)
# Each pose is a 4x4 matrix
poses = [pose1, pose2]  # You will get these from your drone logs

# Example bounding box centers detected (in pixel coordinates)
# Each center corresponds to a barcode detection
bbox_centers = {
    "image1.jpg": np.array([[2100, 1600], [1500, 1700]]),  # multiple barcodes possible
    "image2.jpg": np.array([[2150, 1580], [1550, 1680]]),
}

# Match barcodes manually or based on proximity (simple for now)
# Assume first in image1 matches first in image2, etc.

def triangulate_points(K, pose1, pose2, pts1, pts2):
    R1, t1 = pose1[:3, :3], pose1[:3, 3]
    R2, t2 = pose2[:3, :3], pose2[:3, 3]

    P1 = K @ np.hstack((R1, t1.reshape(3, 1)))
    P2 = K @ np.hstack((R2, t2.reshape(3, 1)))

    pts4d_hom = cv2.triangulatePoints(P1, P2, pts1.T, pts2.T)
    pts3d = (pts4d_hom / pts4d_hom[3])[:3].T

    return pts3d

# Collect matching points
pts1 = bbox_centers["image1.jpg"]
pts2 = bbox_centers["image2.jpg"]

# Triangulate all points
pts3d = triangulate_points(K, poses[0], poses[1], pts1, pts2)

# Build dictionary
barcode_dict = {}
for i, pt in enumerate(pts3d):
    barcode_id = f"barcode_{i+1}"
    barcode_dict[barcode_id] = pt.tolist()

# --- New Part: Calculate drone observation points ---
# Assumption: all barcodes lie on (approximate) plane
# Fit plane to barcode 3D points

def fit_plane(points):
    centroid = np.mean(points, axis=0)
    u, s, vh = np.linalg.svd(points - centroid)
    normal = vh[2, :]
    return centroid, normal

barcode_positions = np.array(list(barcode_dict.values()))
centroid, normal = fit_plane(barcode_positions)

# Choose fixed distance to stand away from the barcode plane
OBSERVATION_DISTANCE = 2.0  # meters

# For each barcode, calculate desired drone position
waypoints = {}
for barcode_id, position in barcode_dict.items():
    position = np.array(position)
    drone_position = position + normal * OBSERVATION_DISTANCE
    waypoints[barcode_id] = drone_position.tolist()

# Save everything to JSON
output = {
    "barcodes": barcode_dict,
    "waypoints": waypoints
}

with open("barcode_waypoints.json", "w") as f:
    json.dump(output, f, indent=2)

print("Barcode 3D positions and drone waypoints saved to barcode_waypoints.json!")
