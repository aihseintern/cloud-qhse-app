# import cv2, time
# from ultralytics import YOLO
# import numpy as np

# BODY_KEYPOINTS = {
#         "nose": 0,
#         "left_eye": 1,
#         "right_eye": 2,
#         "left_ear": 3,
#         "right_ear": 4,
#         "left_shoulder": 5,
#         "right_shoulder": 6,
#         "left_elbow": 7,
#         "right_elbow": 8,
#         "left_wrist": 9,
#         "right_wrist": 10,
#         "left_hip": 11,
#         "right_hip": 12,
#         "left_knee": 13,
#         "right_knee": 14,
#         "left_ankle": 15,
#         "right_ankle": 16
#     }

# X_POS = 0
# Y_POS = 1
# CONF = 2


# def calculate_angle(a, b, c):
#     """
#     Calculate the angle between three points (in 2D).
#     Points should be passed as tuples (x, y).
#     a: First point (e.g., shoulder)
#     b: Middle point (e.g., elbow)
#     c: Last point (e.g., wrist)
    
#     Returns the angle in degrees.
#     """
#     # Convert points to vectors
#     ab = np.array(a) - np.array(b)
#     bc = np.array(c) - np.array(b)
    
#     # Calculate the dot product and magnitudes of the vectors
#     dot_product = np.dot(ab, bc)
#     magnitude_ab = np.linalg.norm(ab)
#     magnitude_bc = np.linalg.norm(bc)
    
#     # Calculate the cosine of the angle
#     cos_theta = dot_product / (magnitude_ab * magnitude_bc)
    
#     # Ensure the value is in the valid range for arccos (-1, 1)
#     cos_theta = np.clip(cos_theta, -1.0, 1.0)
    
#     # Calculate the angle in radians and convert to degrees
#     angle = np.arccos(cos_theta)
#     angle_degrees = np.degrees(angle)
    
#     return angle_degrees


# def is_wrist_facing_up(elbow, wrist, shoulder):
#     """
#     Check if the wrist is facing up relative to the elbow.
#     """
#     return wrist[Y_POS] < elbow[Y_POS] and wrist[Y_POS] < shoulder[Y_POS]


# def are_wrist_keypoints_close(wrist1, wrist2, threshold=30):
#     distance = np.sqrt((wrist1[X_POS] - wrist2[X_POS]) ** 2 + (wrist1[Y_POS] - wrist2[Y_POS]) ** 2)
#     return distance < threshold

# def are_wrist_keypoints_same(wrist1, wrist2, tolerance=5):
#     return abs(wrist1[X_POS] - wrist2[X_POS]) < tolerance and abs(wrist1[Y_POS] - wrist2[Y_POS]) < tolerance

# def is_keypoint_confident(keypoint, min_confidence=0.5):
#     return keypoint[CONF] >= min_confidence


# Load the YOLOv8 model for pose detection
# model = YOLO('yolov8n-pose.pt')  # Ensure you have the YOLOv8 pose model downloaded
# model.to('cuda')

# url = 'http://192.168.8.9:4747/video'

# # Open the webcam
# cap = cv2.VideoCapture(url)

# while True:
#     # Read frame from webcam
#     ret, frame = cap.read()
#     if not ret:
#         break

#     # Perform pose detection
#     results = model(frame)

#     # Draw results on the frame
#     annotated_frame = results[0].plot()
    
    # Loop through each detected object
    # for obj_idx in range(len(results[0].keypoints)):
    #     keypoints = results[0].keypoints[obj_idx].data[0]
        
    #     print('keypointssssssss')
    #     print(keypoints)

    #     # Ensure keypoints exist and are not empty
    #     if keypoints is not None and keypoints.size(0) > 0:
            
#             # Get the keypoints for the right shoulder, right elbow, and right wrist
#             right_shoulder = keypoints[BODY_KEYPOINTS["right_shoulder"]][:2].tolist()
#             right_elbow = keypoints[BODY_KEYPOINTS["right_elbow"]][:2].tolist()
#             right_wrist = keypoints[BODY_KEYPOINTS["right_wrist"]][:2].tolist()
            
#             # Get the keypoints for the left shoulder, left elbow, and left wrist
#             left_shoulder = keypoints[BODY_KEYPOINTS["left_shoulder"]][:2].tolist()
#             left_elbow = keypoints[BODY_KEYPOINTS["left_elbow"]][:2].tolist()
#             left_wrist = keypoints[BODY_KEYPOINTS["left_wrist"]][:2].tolist()

#             # Calculate the angle at the right elbow
#             right_elbow_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)
            
#             # Calculate the angle at the left elbow
#             left_elbow_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)
            
#             # Check if the right elbow angle is around 90 degrees and wrist is facing up
#             right_is_strong = 40 <= right_elbow_angle <= 100 and is_wrist_facing_up(right_elbow, right_wrist, right_shoulder)

#             # Check if the left elbow angle is around 90 degrees and wrist is facing up
#             left_is_strong = 40 <= left_elbow_angle <= 100 and is_wrist_facing_up(left_elbow, left_wrist, left_shoulder)
            
#             # Get the head (e.g., nose) keypoint
#             nose = keypoints[BODY_KEYPOINTS["nose"]][:2].tolist()

#             # Display the right elbow angle on the frame
#             cv2.putText(
#                 annotated_frame, 'Right Elbow Angle:',
#                 (int(right_elbow[0]), int(right_elbow[1]) - 30),  # Position for the description
#                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA
#             )

#             cv2.putText(
#                 annotated_frame, f'{right_elbow_angle:.2f} deg',
#                 (int(right_elbow[0]), int(right_elbow[1]) - 10),  # Position for the angle value
#                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA
#             )

#             # Display the left elbow angle on the frame
#             cv2.putText(
#                 annotated_frame, 'Left Elbow Angle:',
#                 (int(left_elbow[0]), int(left_elbow[1]) - 30),  # Position for the description
#                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA
#             )

#             cv2.putText(
#                 annotated_frame, f'{left_elbow_angle:.2f} deg',
#                 (int(left_elbow[0]), int(left_elbow[1]) - 10),  # Position for the angle value
#                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA
#             )
            
#             # Display "STRONG" above the head if both arms are in L shape
#             if right_is_strong and left_is_strong:
#                 cv2.putText(
#                     annotated_frame, 'STRONG',
#                     (int(nose[0]), int(nose[1]) - 40),
#                     cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv2.LINE_AA
#                 )
            
#             if (is_keypoint_confident(keypoints[BODY_KEYPOINTS["right_shoulder"]]) and
#                 is_keypoint_confident(keypoints[BODY_KEYPOINTS["right_elbow"]]) and
#                 is_keypoint_confident(keypoints[BODY_KEYPOINTS["right_wrist"]]) and
#                 is_keypoint_confident(keypoints[BODY_KEYPOINTS["left_shoulder"]]) and
#                 is_keypoint_confident(keypoints[BODY_KEYPOINTS["left_elbow"]]) and
#                 is_keypoint_confident(keypoints[BODY_KEYPOINTS["left_wrist"]])):
#                 # Check if wrists are crossing or very close
#                 if are_wrist_keypoints_close(left_wrist, right_wrist) or are_wrist_keypoints_same(left_wrist, right_wrist):
#                     cv2.putText(
#                         annotated_frame, 'Arms Crossing',
#                         (int(nose[0]), int(nose[1]) - 80),
#                         cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv2.LINE_AA
#                     )

        
#     # Display the frame
#     cv2.imshow('Pose Detection', annotated_frame)
    
#     # time.sleep(1)

#     # Exit on 'q' key press
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# # Release resources
# cap.release()
# cv2.destroyAllWindows()
