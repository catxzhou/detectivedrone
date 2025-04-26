import boto3
import os
import time
import json
from PIL import Image
import numpy as np
from io import BytesIO

def start_model(project_arn, model_arn, version_name, min_inference_units):
    client = boto3.client('rekognition')
    try:
        print('Starting model: ' + model_arn)
        response = client.start_project_version(
            ProjectVersionArn=model_arn,
            MinInferenceUnits=min_inference_units
        )
        project_version_running_waiter = client.get_waiter('project_version_running')
        project_version_running_waiter.wait(ProjectArn=project_arn, VersionNames=[version_name])
        print('✅ Model is running.')
    except Exception as e:
        print('❌ Error starting model:', e)

rekognition_client = boto3.client('rekognition')

def detect_custom_labels(client, model_arn, image_bytes):
    try:
        response = client.detect_custom_labels(
            ProjectVersionArn=model_arn,
            Image={'Bytes': image_bytes}
        )
        return response['CustomLabels']
    except Exception as e:
        print('❌ Detection error:', e)
        return []

def process_pallets_and_sheets(image_path, bounding_boxes, pixel_threshold_min=20, pixel_threshold_max=30):
    image = Image.open(image_path).convert('L')  # Convert to grayscale
    np_image = np.array(image)
    img_width, img_height = image.size

    pallets = []

    for i, bbox in enumerate(bounding_boxes):      
        left = int(bbox['Left'] * img_width)
        top = int(bbox['Top'] * img_height)
        width = int(bbox['Width'] * img_width)
        height = int(bbox['Height'] * img_height)

        cropped = np_image[top:top+height, left:left+width]

        white_pixels = np.sum(cropped > 200)

        sheet_detected = None
        if pixel_threshold_min <= white_pixels <= pixel_threshold_max:
            sheet_detected = {
                'sheet_left': left,
                'sheet_top': top,
                'sheet_width': width,
                'sheet_height': height,
                'white_pixels': white_pixels
            }

        pallet_info = {
            'pallet_index': i,
            'pallet_left': left,
            'pallet_top': top,
            'pallet_width': width,
            'pallet_height': height,
            'sheet_detected': sheet_detected
        }

        pallets.append(pallet_info)

    return pallets

def resize_image_if_needed(image_path, max_size=5242880):
    with open(image_path, 'rb') as img_file:
        image_bytes = img_file.read()
        if len(image_bytes) > max_size:
            image = Image.open(image_path)
            scale_factor = (max_size / len(image_bytes)) ** 0.5  # scale both width and height
            new_width = int(image.width * scale_factor)
            new_height = int(image.height * scale_factor)
            resized_image = image.resize((new_width, new_height))
            buffer = BytesIO()
            resized_image.save(buffer, format="JPEG")
            return buffer.getvalue()
        else:
            return image_bytes

def main():
    project_arn='arn:aws:rekognition:eu-central-1:608495930675:project/DroneData/1745678300111'
    model_arn='arn:aws:rekognition:eu-central-1:608495930675:project/DroneData/version/DroneData.2025-04-26T17.05.36/1745679936041'
    min_inference_units=1 
    version_name='DroneData.2025-04-26T17.05.36'

    #start AWS Rekognition model
    start_model(project_arn, model_arn, version_name, min_inference_units)

    #Folder containing images
    image_folder = '/Users/iclal/Desktop/dev_data'
    pixel_threshold_min = 20
    pixel_threshold_max = 30

    #iterate through all images in the folder 
    for image in os.listdir(image_folder):
       if image.lower().endswith(('.png', '.jpg', '.jpeg')):
        image_path = os.path.join(image_folder, image)
        print(f"Processing image: {image_path}")

        #read images as bytes
        image_bytes = resize_image_if_needed(image_path)

        # Detect custom labels
        custom_labels = detect_custom_labels(rekognition_client, model_arn, image_bytes)

        #extract bounding boxes
        bounding_boxes = [
            label['Geometry']['BoundingBox']
            for label in custom_labels
        ]

        # Process pallets and sheets
        pallets = process_pallets_and_sheets(image_path, bounding_boxes, pixel_threshold_min, pixel_threshold_max)

        # Output the results
        print(f"Results for {image}:")
        print(json.dumps(pallets, indent=4))

if __name__ == "__main__":
    main()