import threading
from utils.detector import BaseDetector
from app.models import DetectedObject
from app.extensions import db
from datetime import datetime
import cv2

from flask import current_app
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
import time

from utils.wa import send_whatsapp_message

class GestureForHelpDetector(BaseDetector):
    def __init__(self):
        super().__init__("weights/Fall Detection Model.pt", "Gesture")

    def process_results(self, results, frame, camera_id):
        with self.app.app_context():
            objects = ""
            # for c in results[0].boxes.cls:
            #     name = self.model.names[int(c)]
            #     if name == "cross-hands":
            #         objects += f"{name}, - "        
            # print(f"Gesture for Help detected on camera {camera_id}.")
            if 0 in results[0].boxes.cls:

                detected_obj = DetectedObject(
                    detector_id=camera_id,
                    name='cross-hands',
                    frame=cv2.imencode('.jpg', frame)[1].tobytes(),
                    timestamp=datetime.now()
                )
                db.session.add(detected_obj)
                db.session.commit()
                
                target = 'Y0L0'
                message = f"Subject: *SOS DETECTED*||• Camera ID: {camera_id}||• Violation: cross-hands||• timestamp: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
                
                image_filename = f"unfocused_{camera_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                image_path = os.path.join(os.getcwd(), image_filename)
                cv2.imwrite(image_path, frame)
                
                # Send the WhatsApp message using the helper function
                threading.Thread(target=send_whatsapp_message, args=(current_app._get_current_object(), target, message, image_path)).start()
        annotated_frame = results[0].plot()
        with self.lock:
            self.frames[camera_id] = annotated_frame
        
        time_interval = 15    
        # time.sleep(time_interval)
        
