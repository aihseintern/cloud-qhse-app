import cv2
from ultralytics import YOLO
import torch

# Step 1: Load the YOLO model (You can specify a different model if needed)
model = YOLO('weights/ppe-sparse.pt')  # Use 'yolov8n.pt' or any other YOLO model you prefer

# Check if the model was loaded correctly
if isinstance(model.model, dict):
    # Convert to a torch model if it's in an incompatible format
    model.model = torch.nn.Module(model.model)
    
checkpoint = torch.load('weights/ppe-sparse.pt', map_location='cpu')
print(checkpoint.keys())  # This will show you the keys in the checkpoint

# Step 2: Initialize the webcam
cap = cv2.VideoCapture(0)  # Use 0 for the default webcam

# Step 3: Start webcam detection
while True:
    # Capture frame from webcam
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame. Exiting...")
        break

    # Step 4: Perform detection
    results = model(frame)

    # Step 5: Annotate the frame with detection results
    annotated_frame = results[0].plot()  # Annotate with bounding boxes and labels

    # Step 6: Display the annotated frame
    cv2.imshow('YOLO Webcam Detection', annotated_frame)

    # Step 7: Exit on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Step 8: Release resources
cap.release()
cv2.destroyAllWindows()
