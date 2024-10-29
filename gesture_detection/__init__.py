# import threading
# import cv2
# from flask_login import current_user
# import numpy as np
# from datetime import datetime
# from gesture_detection.gesture import Gesture
# from utils.detector import BaseDetector
# from app.models import DetectedObject, Detector
# from app.extensions import db
# from flask import current_app, session
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# import os
# import time
# from utils.wa import Message, send_whatsapp_message
# from ultralytics import YOLO

# class GestureForHelpDetector(BaseDetector):
#     def __init__(self):
#         super().__init__("Gesture")
#         self.gesture = Gesture()

#     def process_results(self, results, frame, detector_id):   
#         self.load_weight(detector_id)

#         with self.app.app_context():
#             session_role = session.get('role')
#             objects = ""

#             # Run pose detection
#             pose_results = self.model(frame)
#             annotated_frame = pose_results[0].plot()
#             for obj_idx in range(len(pose_results[0].keypoints)):
#                 track_id = pose_results[0].boxes[obj_idx].id
#                 track_id = int(track_id.item())  # Convert from tensor to int
                
#                 keypoints = pose_results[0].keypoints[obj_idx].data[0]
#                 self.gesture.keypoints = keypoints
#                 # Ensure keypoints exist and are not empty
#                 if keypoints is not None and keypoints.size(0) > 0:
                    
#                     keypoints_dict = self.gesture.get_keypoints()
                    
#                     # Calculate elbow angles using keypoints_dict
#                     right_elbow_angle = self.calculate_angle(keypoints_dict['right_shoulder'], 
#                                                             keypoints_dict['right_elbow'], 
#                                                             keypoints_dict['right_wrist'])

#                     left_elbow_angle = self.calculate_angle(keypoints_dict['left_shoulder'], 
#                                                             keypoints_dict['left_elbow'], 
#                                                             keypoints_dict['left_wrist'])

#                     # Annotate the right elbow angle on the frame
#                     cv2.putText(
#                         annotated_frame, 'Right Elbow Angle:',
#                         (int(keypoints_dict['right_elbow'][0]), int(keypoints_dict['right_elbow'][1]) - 30),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA
#                     )
#                     cv2.putText(
#                         annotated_frame, f'{right_elbow_angle:.2f} deg',
#                         (int(keypoints_dict['right_elbow'][0]), int(keypoints_dict['right_elbow'][1]) - 10),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA
#                     )

#                     # Annotate the left elbow angle on the frame
#                     cv2.putText(
#                         annotated_frame, 'Left Elbow Angle:',
#                         (int(keypoints_dict['left_elbow'][0]), int(keypoints_dict['left_elbow'][1]) - 30),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA
#                     )
#                     cv2.putText(
#                         annotated_frame, f'{left_elbow_angle:.2f} deg',
#                         (int(keypoints_dict['left_elbow'][0]), int(keypoints_dict['left_elbow'][1]) - 10),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA
#                     )
                    
#                     # get gesture type
#                     gestureName = self.gesture.get_gesture_type()

#                     if gestureName:
#                         cv2.putText(
#                             annotated_frame, gestureName,
#                             (int(keypoints_dict['nose'][0]), int(keypoints_dict['nose'][1]) - 30),  # Fetch nose coordinates from dict
#                             cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv2.LINE_AA
#                         )
                        
#                         # capture
#                         detected_obj = DetectedObject(
#                             detector_id=detector_id,
#                             name=gestureName,
#                             frame=cv2.imencode('.jpg', frame)[1].tobytes(),
#                             timestamp=datetime.now(),
#                             role=session_role
#                         )
                        
#                         # Limit the detecting so it doesn't spam
#                         if track_id is not None:
#                             with self.lock:
#                                 print(f"Initial count: {self.detected_objects_tracker[track_id]['count']}, Last frame: {self.detected_objects_tracker[track_id]['last_frame']}")
                                
#                                 # If first time detection or reset count due to detection gap
#                                 if self.detected_objects_tracker[track_id]["count"] == 0:
#                                     # First detection, send message
#                                     db.session.add(detected_obj)
#                                     self.detected_objects_tracker[track_id]["count"] += 1
                                    
#                                 # Detected again in consecutive frames
#                                 elif self.detected_objects_tracker[track_id]["last_frame"] == self.frame_number - 1:
#                                     self.detected_objects_tracker[track_id]["count"] += 1
                                    
#                                 else:
#                                     # Reset count if there's a gap in detection
#                                     self.detected_objects_tracker[track_id]["count"] = 1

#                                 # Check if the object has been detected for 5 consecutive frames
#                                 if self.detected_objects_tracker[track_id]["count"] >= 15:
#                                     # Send WhatsApp message
#                                     db.session.add(detected_obj)
#                                     self.detected_objects_tracker[track_id]["count"] = 0  # Reset the count after sending the message

#                                 # Update last_frame at the end, regardless of the branch
#                                 self.detected_objects_tracker[track_id]["last_frame"] = self.frame_number
                    
#                     db.session.commit()

#                     # target = "Y0L0"
#                     # message = f"Subject: *SOS DETECTED*||• Camera ID: {detector_id}||• Gesture: {gestureName}||• timestamp: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"

#                     image_filename = f"unfocused_{detector_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
#                     image_path = os.path.join(os.getcwd(), image_filename)
#                     cv2.imwrite(image_path, frame)
                    
#                     for rule in self.notification_rules[detector_id]:                    
#                                 message = Message(rule.message_template.template, detected_obj.to_dict()).render()
#                                 self.add_message_to_queue(current_app._get_current_object(), rule.contact.name, message, image_path)

#                     # threading.Thread(target=send_whatsapp_message, args=(current_app._get_current_object(), target, message, image_path)).start()
            
#             with self.lock:
#                 self.frames[detector_id] = annotated_frame

#             time_interval = 15
#             # time.sleep(time_interval)
