from colorama import Back, Style
import cv2
import numpy as np
from ultralytics import YOLO

class Gesture:
    def __init__(self, frame):    
        self.X_POS = 0
        self.Y_POS = 1
        self.CONF = 2
        self.keypoints = None
        self.BODY_KEYPOINTS = {
            "nose": 0,
            "left_eye": 1,
            "right_eye": 2,
            "left_ear": 3,
            "right_ear": 4,
            "left_shoulder": 5,
            "right_shoulder": 6,
            "left_elbow": 7,
            "right_elbow": 8,
            "left_wrist": 9,
            "right_wrist": 10,
            "left_hip": 11,
            "right_hip": 12,
            "left_knee": 13,
            "right_knee": 14,
            "left_ankle": 15,
            "right_ankle": 16
        }
        self.model = YOLO('yolov8n-pose.pt')
        self.frame = frame
    
    def calculate_angle(self, a, b, c):
        ab = np.array(a) - np.array(b)
        bc = np.array(c) - np.array(b)
        dot_product = np.dot(ab, bc)
        magnitude_ab = np.linalg.norm(ab)
        magnitude_bc = np.linalg.norm(bc)
        cos_theta = dot_product / (magnitude_ab * magnitude_bc)
        cos_theta = np.clip(cos_theta, -1.0, 1.0)
        angle = np.arccos(cos_theta)
        angle_degrees = np.degrees(angle)
        return angle_degrees
    
    def is_wrist_facing_up(self, elbow, wrist, shoulder):
        return wrist[self.Y_POS] < elbow[self.Y_POS] and wrist[self.Y_POS] < shoulder[self.Y_POS]

    def are_wrist_keypoints_close(self, wrist1, wrist2, threshold=30):
        distance = np.sqrt((wrist1[self.X_POS] - wrist2[self.X_POS]) ** 2 + (wrist1[self.Y_POS] - wrist2[self.Y_POS]) ** 2)
        return distance < threshold

    def are_wrist_keypoints_same(self, wrist1, wrist2, tolerance=5):
        return abs(wrist1[self.X_POS] - wrist2[self.X_POS]) < tolerance and abs(wrist1[self.Y_POS] - wrist2[self.Y_POS]) < tolerance

    def is_keypoint_confident(self, keypoint, min_confidence=0.5):
        return keypoint[self.CONF] >= min_confidence
    
    def get_keypoints(self):
        keypoints_dict = {
            "right_shoulder": self.keypoints[self.BODY_KEYPOINTS["right_shoulder"]][:2].tolist(),
            "right_elbow": self.keypoints[self.BODY_KEYPOINTS["right_elbow"]][:2].tolist(),
            "right_wrist": self.keypoints[self.BODY_KEYPOINTS["right_wrist"]][:2].tolist(),
            "left_shoulder": self.keypoints[self.BODY_KEYPOINTS["left_shoulder"]][:2].tolist(),
            "left_elbow": self.keypoints[self.BODY_KEYPOINTS["left_elbow"]][:2].tolist(),
            "left_wrist": self.keypoints[self.BODY_KEYPOINTS["left_wrist"]][:2].tolist(),
            "nose": self.keypoints[self.BODY_KEYPOINTS["nose"]][:2].tolist()
        }
        return keypoints_dict

    
    def get_gesture_type(self):
        keypoints_dict = self.get_keypoints()

        right_elbow_angle = self.calculate_angle(keypoints_dict['right_shoulder'], 
                                                keypoints_dict['right_elbow'], 
                                                keypoints_dict['right_wrist'])

        left_elbow_angle = self.calculate_angle(keypoints_dict['left_shoulder'], 
                                                keypoints_dict['left_elbow'], 
                                                keypoints_dict['left_wrist'])
        
        if self.is_strong(keypoints_dict, right_elbow_angle, left_elbow_angle) == "STRONG":
            return "STRONG"
        
        if self.is_amrs_crossing(keypoints_dict) == "ARMS_CROSSING":
            return "ARMS_CROSSING"
        
        # Return None or a default value if no gesture type matches
        return None

        
    # "Strong" gesture
    def is_strong(self, keypoints_dict, right_elbow_angle, left_elbow_angle):
        right_is_strong = (40 <= right_elbow_angle <= 100 and 
                   self.is_wrist_facing_up(keypoints_dict['right_elbow'], 
                                           keypoints_dict['right_wrist'], 
                                           keypoints_dict['right_shoulder']))

        left_is_strong = (40 <= left_elbow_angle <= 100 and 
                        self.is_wrist_facing_up(keypoints_dict['left_elbow'], 
                                                keypoints_dict['left_wrist'], 
                                                keypoints_dict['left_shoulder']))
        
        if right_is_strong and left_is_strong:
            return "STRONG"
        
    
    # "Arms Crossing" gesture
    def is_amrs_crossing(self, keypoints_dict):
        if (self.is_keypoint_confident(keypoints_dict["right_shoulder"]) and
            self.is_keypoint_confident(keypoints_dict["right_elbow"]) and
            self.is_keypoint_confident(keypoints_dict["right_wrist"]) and
            self.is_keypoint_confident(keypoints_dict["left_shoulder"]) and
            self.is_keypoint_confident(keypoints_dict["left_elbow"]) and
            self.is_keypoint_confident(keypoints_dict["left_wrist"])):
            
            if (self.are_wrist_keypoints_close(keypoints_dict["left_wrist"], keypoints_dict["right_wrist"]) or 
                self.are_wrist_keypoints_same(keypoints_dict["left_wrist"], keypoints_dict["right_wrist"])):
                return "ARMS_CROSSING"

    
    def process_results(self):
        pose_results = self.model.track(self.frame, stream=False, persist=True)
        annotated_frame = pose_results[0].plot()
        for obj_idx in range(len(pose_results[0].keypoints)):
                track_id = pose_results[0].boxes[obj_idx].id
                track_id = int(track_id.item())
                
                self.keypoints = pose_results[0].keypoints[obj_idx].data[0]
                # Ensure keypoints exist and are not empty
                if self.keypoints is not None and self.keypoints.size(0) > 0:
                    
                    keypoints_dict = self.get_keypoints()
                    
                    # Calculate elbow angles using keypoints_dict
                    right_elbow_angle = self.calculate_angle(keypoints_dict['right_shoulder'], 
                                                            keypoints_dict['right_elbow'], 
                                                            keypoints_dict['right_wrist'])

                    left_elbow_angle = self.calculate_angle(keypoints_dict['left_shoulder'], 
                                                            keypoints_dict['left_elbow'], 
                                                            keypoints_dict['left_wrist'])

                    # Annotate the right elbow angle on the frame
                    cv2.putText(
                        annotated_frame, 'Right Elbow Angle:',
                        (int(keypoints_dict['right_elbow'][0]), int(keypoints_dict['right_elbow'][1]) - 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA
                    )
                    cv2.putText(
                        annotated_frame, f'{right_elbow_angle:.2f} deg',
                        (int(keypoints_dict['right_elbow'][0]), int(keypoints_dict['right_elbow'][1]) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA
                    )

                    # Annotate the left elbow angle on the frame
                    cv2.putText(
                        annotated_frame, 'Left Elbow Angle:',
                        (int(keypoints_dict['left_elbow'][0]), int(keypoints_dict['left_elbow'][1]) - 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA
                    )
                    cv2.putText(
                        annotated_frame, f'{left_elbow_angle:.2f} deg',
                        (int(keypoints_dict['left_elbow'][0]), int(keypoints_dict['left_elbow'][1]) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA
                    )
                    
                    gestureName = self.get_gesture_type()
                    
                    if gestureName:
                        cv2.putText(
                            annotated_frame, gestureName,
                            (int(keypoints_dict['nose'][0]), int(keypoints_dict['nose'][1]) - 30),  # Fetch nose coordinates from dict
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv2.LINE_AA
                        )
        return annotated_frame, gestureName
