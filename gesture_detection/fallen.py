import cv2
import numpy as np
from ultralytics import YOLO

class Fallen:
    BODY_KEYPOINTS = {
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

    POSE_PAIRS = [
        ("left_shoulder", "right_shoulder"), ("left_shoulder", "left_elbow"), ("right_shoulder", "right_elbow"),
        ("left_elbow", "left_wrist"), ("right_elbow", "right_wrist"),
        ("left_hip", "right_hip"), ("left_shoulder", "left_hip"), ("right_shoulder", "right_hip"),
        ("left_hip", "left_knee"), ("right_hip", "right_knee"),
        ("left_knee", "left_ankle"), ("right_knee", "right_ankle")
    ]

    def __init__(self, frame):
        self.frame = frame
        self.model = YOLO('../models/yolo11n-pose.pt')
        self.model.to('cpu')
        self.keypoints = None

    def is_fallen(self):
        left_hip = self.keypoints[self.BODY_KEYPOINTS["left_hip"]][:2].tolist()
        right_hip = self.keypoints[self.BODY_KEYPOINTS["right_hip"]][:2].tolist()
        left_shoulder = self.keypoints[self.BODY_KEYPOINTS["left_shoulder"]][:2].tolist()
        right_shoulder = self.keypoints[self.BODY_KEYPOINTS["right_shoulder"]][:2].tolist()

        height = np.linalg.norm(np.array(left_hip) - np.array(right_hip))
        width = np.linalg.norm(np.array(left_shoulder) - np.array(right_shoulder))

        return height / width < 0.8 and self.keypoints[self.BODY_KEYPOINTS["left_hip"]][1] < self.keypoints[self.BODY_KEYPOINTS["left_shoulder"]][1]

    def draw_pose(self, annotated_frame):
        for pair in self.POSE_PAIRS:
            part_a, part_b = pair
            idx_a, idx_b = self.BODY_KEYPOINTS[part_a], self.BODY_KEYPOINTS[part_b]
            if self.keypoints[idx_a][2] > 0.5 and self.keypoints[idx_b][2] > 0.5:
                point_a = (int(self.keypoints[idx_a][0]), int(self.keypoints[idx_a][1]))
                point_b = (int(self.keypoints[idx_b][0]), int(self.keypoints[idx_b][1]))
                cv2.line(annotated_frame, point_a, point_b, (0, 255, 255), 2)

    def draw_keypoints(self, annotated_frame):
        for part, idx in self.BODY_KEYPOINTS.items():
            x, y, conf = self.keypoints[idx][:3].tolist()
            if conf > 0.5:
                cv2.circle(annotated_frame, (int(x), int(y)), 5, (0, 0, 255), -1)

    def process_results(self):
        results = self.model(self.frame)
        annotated_frame = self.frame.copy()
        status = "No Detection"

        for obj_idx in range(len(results[0].keypoints)):
            self.keypoints = results[0].keypoints[obj_idx].data[0]

            if self.keypoints is not None and self.keypoints.size(0) > 0:
                status = "Stable"
                box_color = (0, 255, 0)

                if self.is_fallen():
                    status = "Fallen"
                    box_color = (0, 0, 255)

                x1, y1, x2, y2 = map(int, results[0].boxes[obj_idx].xyxy[0].tolist())
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), box_color, 2)

                self.draw_pose(annotated_frame)
                self.draw_keypoints(annotated_frame)

                cv2.putText(
                    annotated_frame, status,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, box_color, 2, cv2.LINE_AA
                )

        return annotated_frame, status

# Video capture and display loop
# cap = cv2.VideoCapture(0)

# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     fallen_detector = Fallen(frame)
#     annotated_frame = fallen_detector.process_frame()

#     cv2.imshow('Pose Detection', annotated_frame)

#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()
