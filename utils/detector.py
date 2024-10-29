import os
import re
# from telnetlib import EC
import time
from colorama import Back, Style
import cv2
from flask_login import current_user
from ultralytics import YOLO
from app.models import CCTV, Contact, Detector, DetectedObject, DetectorType, MessageTemplate, NotificationRule, Weight
import threading
from datetime import datetime
import time
import queue
# from utils.wa import send_whatsapp_message
from collections import defaultdict
import threading
import cv2
import time
import logging

from utils.message import Message

# Setup logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='detector.log')

message_queue = queue.Queue()

annotated_frames = {}

class CameraStreamManager:
    def __init__(self):
        self.camera_streams = {}
        self.lock = threading.Lock()

    def get_camera_stream(self, ip_address):
        with self.lock:
            if ip_address not in self.camera_streams:
                # Start new thread for the camera if not already started
                logging.info(f"Starting new camera stream for IP: {ip_address}")
                camera_stream = CameraStream(ip_address)
                camera_stream.start()
                self.camera_streams[ip_address] = camera_stream
            return self.camera_streams[ip_address]

    def stop_all(self):
        with self.lock:
            logging.info("Stopping all camera streams.")
            for camera_stream in self.camera_streams.values():
                camera_stream.stop()
                camera_stream.join()
            self.camera_streams.clear()

class CameraStream(threading.Thread):
    def __init__(self, ip_address):
        super().__init__(name=f"CameraStream-{ip_address}")
        self.ip_address = ip_address
        self.capture = cv2.VideoCapture(0) if ip_address == 'http://0.0.0.0' else cv2.VideoCapture(ip_address)
        self.capture.set(cv2.CAP_PROP_FPS, 30)
        # if not self.capture.isOpened():
        #     logging.error(f"Failed to open camera stream for IP: {self.ip_address}")
        #     self.stop()
        while not self.capture.isOpened():
            logging.error(f"Failed to open camera stream for IP: {self.ip_address}")
            time.sleep(5)
            logging.info(f"Retrying to open camera stream for IP: {self.ip_address}")
            self.capture = cv2.VideoCapture(ip_address)
            self.capture.set(cv2.CAP_PROP_FPS, 30)

        self.frame = None
        self.running = True
        self.lock = threading.Lock()
        logging.info(f"Initialized CameraStream for IP: {self.ip_address}")

    def run(self):
        logging.info(f"Camera stream started for IP: {self.ip_address}")
        while self.running:
            ret, frame = self.capture.read()
            if ret:
                with self.lock:
                    self.frame = frame
            else:
                logging.warning(f"Failed to read frame from IP: {self.ip_address}")
                time.sleep(1)  # Retry after a short delay
                self._reconnect()
    
    def _reconnect(self):
        if self.running:
            logging.info(f"Reconnecting to camera stream for IP: {self.ip_address}")
            self.capture.release()
            time.sleep(2)  # Small delay before reconnecting
            self.capture = cv2.VideoCapture(self.ip_address)
            self.capture.set(cv2.CAP_PROP_FPS, 30)
            while not self.capture.isOpened():
                logging.error(f"Failed to reopen camera stream for IP: {self.ip_address}")
                time.sleep(5)
                logging.info(f"Retrying to open camera stream for IP: {self.ip_address}")
                self.capture = cv2.VideoCapture(self.ip_address)
                self.capture.set(cv2.CAP_PROP_FPS, 30)

    def get_frame(self):
        with self.lock:
            return self.frame

    def stop(self):
        self.running = False
        if self.capture:
            self.capture.release()
        logging.info(f"Camera stream stopped and resources released for IP: {self.ip_address}")

class DetectorThread(threading.Thread):
    global annotated_frames

    def __init__(self, app, detector_id, camera_stream, notification_rules):
        super().__init__(name=f"DetectorThread-{detector_id}")
        self.app = app
        self.detector_id = detector_id
        self.camera_stream = camera_stream
        self.running = True
        self.notification_rules = notification_rules
        self.detected_objects_tracker = defaultdict(lambda: {"count": 0, "last_time": 0})
        self.boxes_id = []
        self.lock = threading.Lock()
        logging.info(f"Initialized DetectorThread for detector ID: {self.detector_id}")

    def run(self):
        logging.info(f"DetectorThread started for detector ID: {self.detector_id}")
        while self.running:
            frame = self.camera_stream.get_frame()
            if frame is not None:
                with self.app.app_context():
                    detector = Detector.query.get(self.detector_id)
                    try:
                        # self.detected_objects_tracker['last_time'] = time.time()
                        detected_objects_tracker = self.detected_objects_tracker
                        with self.lock:
                            detected_objects, annotated_frame, self.detected_objects_tracker, self.boxes_id = detector.process_frame(frame, detected_objects_tracker, self.boxes_id)

                            # Check if there are any detected obj
                            print(f"self boxes id {self.boxes_id}")
                            if self.boxes_id:
                                annotated_frames[self.detector_id] = annotated_frame
                                # logging.info(f"Detector {detector.id} detected objects: {detected_objects}")
                                # Add the message to the shared queue
                                image_filename = f"detected_{detector.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                                upload_dir = os.path.join(os.getcwd(), 'detected_objects')
                                image_path = os.path.join(upload_dir, image_filename)                         
                                if detected_objects:    
                                    cv2.imwrite(image_path, annotated_frame)
                                    for detected_object in detected_objects:
                                        for rule in self.notification_rules[self.detector_id]:
                                            # add new dict var called queue length to the detected object dict
                                            queue_length = message_queue.qsize()
                                            detected_object['queue_length'] = queue_length
                                            # Query the NotificationRule instance again within the same session context
                                            rule = NotificationRule.query.get(rule.id)
                                            template = rule.message_template.template
                                            message = Message(template, detected_object).render()                                   
                                            message_queue.put((rule.contact.name, message, image_path))  # Add message to the queue
                                            print("add msg to q")
                    except Exception as e:
                        logging.error(f"Error processing frame for detector ID: {self.detector_id}: {e}")
                    finally:
                        time.sleep(1)
            else:
                logging.warning(f"No frame available for detector ID: {self.detector_id}")

    def stop(self):
        self.running = False
        logging.info(f"DetectorThread stopped for detector ID: {self.detector_id}")

class DetectorManager:
    
    def __init__(self, session):
        self.session = session
        self.detectors = {}
        self.camera_manager = CameraStreamManager()
        self.lock = threading.Lock()
        self.app = None
        self.notification_rules = {}
        self.message_sender_thread = None

    def initialize_detectors(self, app):
        self.app = app
        self.message_sender_thread = MessageSenderThread(self.app, message_queue)
        self.message_sender_thread.start()
        with self.app.app_context():
            with self.lock:
                logging.info("Initializing detectors...")
                active_detectors = get_active_detectors()
                for detector in active_detectors:
                    cctv = CCTV.query.get(detector.cctv_id)
                    if cctv.status:
                        self.notification_rules[detector.id] = get_notification_rules(detector.id)
                        # Get the shared camera stream for this IP address
                        camera_stream = self.camera_manager.get_camera_stream(cctv.ip_address)

                        # Start a separate thread for each detector processing the frame
                        detector_thread = DetectorThread(self.app, detector.id, camera_stream, self.notification_rules)
                        detector_thread.start()

                        self.detectors[detector.id] = detector_thread
                        logging.info(f"Detector {detector.id} started with camera stream {cctv.ip_address}")
                    else:
                        logging.warning(f"Camera stream for CCTV ID {cctv.id} is not active. Stopping detector {detector.id}")
                        detector.stop()
                        
    def update_detectors(self):
        with self.app.app_context():
            with self.lock:
                logging.info("Updating detectors...")
                active_detectors = get_active_detectors()
                logging.info(f"Active detectors: {active_detectors}")
                active_detector_ids = {detector.id for detector in active_detectors}                

                # Stop detectors that are no longer active
                to_stop = [detector_id for detector_id in self.detectors if detector_id not in active_detector_ids]
                for detector_id in to_stop:
                    logging.info(f"Stopping detector ID: {detector_id}")
                    self.detectors[detector_id].stop()
                    del self.detectors[detector_id]

                # Start new detectors
                for detector in active_detectors:
                    if detector.id not in self.detectors:
                        cctv = CCTV.query.get(detector.cctv_id)
                        if cctv.status:
                            self.notification_rules[detector.id] = get_notification_rules(detector.id)
                            camera_stream = self.camera_manager.get_camera_stream(cctv.ip_address)
                            detector_thread = DetectorThread(self.app, detector.id, camera_stream, self.notification_rules)
                            detector_thread.start()
                            self.detectors[detector.id] = detector_thread
                            logging.info(f"Started new detector ID: {detector.id} with camera stream {cctv.ip_address}")
                        else:
                            logging.warning(f"Camera stream for CCTV ID {cctv.id} is not active. Stopping detector {detector.id}")
                            detector.stop()

                # Stop camera no longer used
                active_camera_ips = {CCTV.query.get(detector.cctv_id).ip_address for detector in active_detectors}
                to_stop = [ip_address for ip_address in self.camera_manager.camera_streams if ip_address not in active_camera_ips]

                for ip_address in to_stop:
                    logging.info(f"Stopping camera stream for IP: {ip_address}")
                    self.camera_manager.camera_streams[ip_address].stop()
                    self.camera_manager.camera_streams[ip_address].join()
                    del self.camera_manager.camera_streams[ip_address]

    def stop_all(self):
        with self.lock:
            logging.info("Stopping all detectors.")
            for detector_thread in self.detectors.values():
                detector_thread.stop()
                detector_thread.join()
            self.detectors.clear()
            self.camera_manager.stop_all()
            if self.message_sender_thread is not None:
                self.message_sender_thread.stop()
                self.message_sender_thread.join()
                self.message_sender_thread = None
            logging.info("All detectors and message sender thread stopped.")

class MessageSenderThread(threading.Thread):
    def __init__(self, app, message_queue):
        super().__init__(name="MessageSenderThread")
        self.app = app
        self.message_queue = message_queue
        self.running = True
        logging.info("Initialized MessageSenderThread")

    def run(self):
        logging.info("MessageSenderThread started")
        while self.running:
            try:
                target_name, message, image_path = self.message_queue.get(timeout=1)
                with self.app.app_context():
                    Message.send_whatsapp_message(target_name, message, image_path)
                self.message_queue.task_done()
                time.sleep(3)
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Error sending message: {e}")

    def stop(self):
        self.running = False
        # Clear the queue to ensure the thread exits promptly
        with self.message_queue.mutex:
            self.message_queue.queue.clear()
        self.message_queue.join()           
        logging.info("MessageSenderThread stopped")
# Query untuk mendapatkan semua detektor yang aktif
def get_active_detectors():
    # Fungsi ini perlu dikonfigurasi sesuai dengan implementasi database Anda
    logging.info("Fetching active detectors from the database.")
    return Detector.query.filter(Detector.running == True).all()

def get_notification_rules(detector_id):
    logging.info(f"Fetching notification rules for detector ID: {detector_id}")
    return NotificationRule.query.join(Detector).join(MessageTemplate).join(Contact).filter(Detector.id == detector_id).all()
    