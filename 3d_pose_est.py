import numpy as np
import cv2
import json

# Camera intrinsic matrix
K = np.array([
    [2804.051, 0, 2010.41],
    [0, 2804.051, 1512.734],
    [0, 0, 1]
])

# Distortion coefficients (not used here but good to have)
dist_coeffs = np.array([0.116413456, -0.202624237, 0.136982457, 0.000004293, -0.000216595])

def get_bbox_centers(bboxes):
    """
    Compute center points from bounding boxes.
    """
    centers = []
    for bbox in bboxes:
        xmin, ymin, xmax, ymax = bbox
        center_x = (xmin + xmax) / 2
        center_y = (ymin + ymax) / 2
        centers.append(np.array([center_x, center_y]))
    return centers

def triangulate_points(K, pose1, pose2, pts1, pts2):
    """
    Triangulate 3D points from two views.
    """
    R1, t1 = pose1[:3, :3], pose1[:3, 3]
    R2, t2 = pose2[:3, :3], pose2[:3, 3]

    P1 = K @ np.hstack((R1, t1.reshape(3, 1)))
    P2 = K @ np.hstack((R2, t2.reshape(3, 1)))

    pts4d_hom = cv2.triangulatePoints(P1, P2, pts1.T, pts2.T)
    pts3d = (pts4d_hom / pts4d_hom[3])[:3].T  # Convert from homogeneous
    return pts3d

# ---- MAIN ----

# Example data

# Read images (you would replace with actual images)
# image1 = cv2.imread('image1.png')
# image2 = cv2.imread('image2.png')

# Assume you already have camera poses from metadata
pose1 = np.eye(4)  # Example: starting pose
pose2 = np.eye(4)
pose2[:3, 3] = np.array([1.0, 0.0, 0.0])  # Example: drone moved 1m to right

# Get bounding boxes from teammate's detector (stub example)
bboxes_img1 = [
    [2000, 1500, 2100, 1600],  # xmin, ymin, xmax, ymax for palette 1
    [2200, 1550, 2300, 1650],  # palette 2
]
bboxes_img2 = [
    [2020, 1520, 2120, 1620],  # palette 1 slightly shifted
    [2220, 1570, 2320, 1670],  # palette 2 slightly shifted
]

# 1. Find centers
centers_img1 = get_bbox_centers(bboxes_img1)
centers_img2 = get_bbox_centers(bboxes_img2)

# 2. Match and Triangulate
barcode_waypoints = {}

for idx, (center1, center2) in enumerate(zip(centers_img1, centers_img2)):
    pts1 = np.array([center1])
    pts2 = np.array([center2])

    pts3d = triangulate_points(K, pose1, pose2, pts1, pts2)

    # Save into dictionary
    barcode_waypoints[f'palette_{idx+1}'] = {
        'barcode': pts3d[0].tolist()
    }

# 3. Save to JSON
with open('barcode_waypoints.json', 'w') as f:
    json.dump(barcode_waypoints, f, indent=2)

print("Saved 3D barcode positions to barcode_waypoints.json!")
