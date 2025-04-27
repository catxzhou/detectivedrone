# detectivedrone
Welcome to the DroneData Processing Pipeline! 

This project combines AWS Rekognition, image processing, and trajectory optimization to automate:

Detection of pallets and sheets from drone-captured images 
Planning an optimized flight path for a drone to scan barcodes efficiently 
It's built to enable intelligent warehouse mapping, inventory management, or any drone-based scanning scenario.


# Features
- AWS Rekognition Integration: Start and use a custom-trained model to detect pallets.
- Image Analysis: Analyze bounding boxes to detect if a "sheet" (white cover) is present.
- Dynamic Image Resizing: Ensure image size meets AWS Rekognition API limits.
- 2-Opt Trajectory Optimization: Efficiently plan drone flight routes to minimize time and battery usage.
- Path Generation: Creates realistic waypoint paths with timestamps and battery estimates.


# How to Run

### Install dependencies:
> pip install boto3 pillow numpy opencv-python
### Set up AWS credentials: Ensure your AWS credentials are configured (e.g., ~/.aws/credentials file or environment variables).
### Prepare your project variables: In the main() function, adjust:
project_arn
model_arn
version_name
image_folder (path to your images)
### Run the program:
python your_script_name.py
### View the results:
Detected pallets and sheets printed in the console.
Optimized drone flight paths generated based on barcode positions.
