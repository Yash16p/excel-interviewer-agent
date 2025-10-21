import cv2
import mediapipe as mp
import numpy as np
from typing import Dict, List

class VisionModule:
    def __init__(self):
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_detection = self.mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5)
        self.face_mesh = self.mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=2, min_detection_confidence=0.5)
    
    def analyze_frame(self, frame: np.ndarray) -> Dict:
        """Comprehensive frame analysis for proctoring"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        analysis = {
            "face_count": self._count_faces(rgb_frame),
            "face_present": False,
            "eye_gaze_direction": None,
            "head_pose": None,
            "anomalies": []
        }
        
        # Face detection
        face_results = self.face_detection.process(rgb_frame)
        if face_results.detections:
            analysis["face_present"] = True
            analysis["face_count"] = len(face_results.detections)
            
            if analysis["face_count"] > 1:
                analysis["anomalies"].append("multiple_faces_detected")
        
        # Eye gaze and head pose analysis
        mesh_results = self.face_mesh.process(rgb_frame)
        if mesh_results.multi_face_landmarks:
            for face_landmarks in mesh_results.multi_face_landmarks:
                gaze_direction = self._estimate_gaze_direction(face_landmarks)
                head_pose = self._estimate_head_pose(face_landmarks)
                
                analysis["eye_gaze_direction"] = gaze_direction
                analysis["head_pose"] = head_pose
                
                # Check for suspicious gaze patterns
                if gaze_direction and abs(gaze_direction["horizontal"]) > 0.7:
                    analysis["anomalies"].append("looking_away")
        
        return analysis
    
    def _count_faces(self, frame: np.ndarray) -> int:
        """Count number of faces in frame"""
        results = self.face_detection.process(frame)
        return len(results.detections) if results.detections else 0
    
    def _estimate_gaze_direction(self, face_landmarks) -> Dict:
        """Estimate eye gaze direction"""
        # Simplified gaze estimation using landmark positions
        # In production, use more sophisticated eye tracking
        return {"horizontal": 0.0, "vertical": 0.0}
    
    def _estimate_head_pose(self, face_landmarks) -> Dict:
        """Estimate head pose (pitch, yaw, roll)"""
        # Simplified head pose estimation
        return {"pitch": 0.0, "yaw": 0.0, "roll": 0.0}
    
    def detect_screen_sharing(self, frame: np.ndarray) -> bool:
        """Detect if screen sharing or secondary displays are visible"""
        # Placeholder for screen sharing detection
        return False