# import cv2
# from ultralytics import YOLO

# # Load the YOLOv8 model for pose detection
# model = YOLO('pose.pt')  # Ensure you have the YOLOv8 pose model downloaded
# model.to('cuda')
# # Open the webcam
# cap = cv2.VideoCapture(0)

# while True:
#     # Read frame from webcam
#     ret, frame = cap.read()
#     if not ret:
#         break

#     # Perform pose detection
#     pose_results = model.track(frame)

#     # Draw results on the frame
#     annotated_frame = pose_results[0].plot()

#     # Display the frame
#     cv2.imshow('Pose Detection', annotated_frame)
    
#     for c in pose_results[0].boxes:
#         track_id = c.id if hasattr(c, 'id') else None
#         print("track id boxes")
#         print(track_id)
        
#     for obj_idx in range(len(pose_results[0].keypoints)):
#         track_id = pose_results[0].boxes[obj_idx].id
#         print("track id keypoints")
#         print(track_id)

#     # Exit on 'q' key press
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# # Release resources
# cap.release()
# cv2.destroyAllWindows()


# # """
# # In the default YOLOv8 pose model, there are 17 keypoints, 
# # each representing a different part of the human body. 
# # Here is the mapping of each index to its respective body joint:

# # 0: Nose 1: Left Eye 2: Right Eye 3: Left Ear 4: Right Ear 
# # 5: Left Shoulder 6: Right Shoulder 7: Left Elbow 8: Right Elbow 
# # 9: Left Wrist 10: Right Wrist 11: Left Hip 12: Right Hip 13: Left Knee 
# # 14: Right Knee 15: Left Ankle 16: Right Ankle

# # A class for storing and manipulating inference results.

# #     This class encapsulates the functionality for handling detection, segmentation, pose estimation,
# #     and classification results from YOLO models.

# #     Attributes:
# #         orig_img (numpy.ndarray): Original image as a numpy array.
# #         orig_shape (Tuple[int, int]): Original image shape in (height, width) format.
# #         boxes (Boxes | None): Object containing detection bounding boxes.
# #         masks (Masks | None): Object containing detection masks.
# #         probs (Probs | None): Object containing class probabilities for classification tasks.
# #         keypoints (Keypoints | None): Object containing detected keypoints for each object.
# #         obb (OBB | None): Object containing oriented bounding boxes.
# #         speed (Dict[str, float | None]): Dictionary of preprocess, inference, and postprocess speeds.
# #         names (Dict[int, str]): Dictionary mapping class IDs to class names.
# #         path (str): Path to the image file.
# #         _keys (Tuple[str, ...]): Tuple of attribute names for internal use.

# #     Methods:
# #         update: Updates object attributes with new detection results.
# #         cpu: Returns a copy of the Results object with all tensors on CPU memory.
# #         numpy: Returns a copy of the Results object with all tensors as numpy arrays.
# #         cuda: Returns a copy of the Results object with all tensors on GPU memory.
# #         to: Returns a copy of the Results object with tensors on a specified device and dtype.
# #         new: Returns a new Results object with the same image, path, and names.
# #         plot: Plots detection results on an input image, returning an annotated image.
# #         show: Shows annotated results on screen.
# #         save: Saves annotated results to file.
# #         verbose: Returns a log string for each task, detailing detections and classifications.
# #         save_txt: Saves detection results to a text file.
# #         save_crop: Saves cropped detection images.
# #         tojson: Converts detection results to JSON format.

# #     Examples:
# #         >>> results = model("path/to/image.jpg")
# #         >>> for result in results:
# #         ...     print(result.boxes)  # Print detection boxes
# #         ...     result.show()  # Display the annotated image
# #         ...     result.save(filename='result.jpg')  # Save annotated image
# # """