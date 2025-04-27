from detect_pallets_barcodes import main as detect_pallets
from post_est_3d import compute_barcode_positions, triangulate_barcodes
from flight_optimization import create_optimized_trajectory
from generate_kfz import export_kfz  # Assuming you have a KFZ export script


def main():
    # Step 1: Detect pallets and barcodes
    pallets_detection = detect_pallets()

    # Step 2: Compute 2D barcode positions
    barcode_positions_2d = compute_barcode_positions(pallets_detection)

    # Step 3: Triangulate to get 3D barcode positions
    barcode_positions_3d = triangulate_barcodes(barcode_positions_2d)

    # Step 4: Plan optimized flight trajectory
    trajectory = create_optimized_trajectory(barcode_positions_3d)

    # Step 5: Export the trajectory as a KFZ file (for the drone)
    export_kfz(trajectory)

    print("Flight plan generated successfully!")


if __name__ == "__main__":
    main()
