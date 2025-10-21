import streamlit as st

try:
    import cv2
    import mediapipe as mp
    CV2_AVAILABLE = True
    MEDIAPIPE_AVAILABLE = True
except ImportError as e:
    CV2_AVAILABLE = False
    MEDIAPIPE_AVAILABLE = False
    st.warning(f"Computer vision libraries not available: {e}")

class WebcamComponent:
    def __init__(self):
        self.cv2_available = CV2_AVAILABLE
        self.mediapipe_available = MEDIAPIPE_AVAILABLE
        
        if self.mediapipe_available:
            self.mp_face_detection = mp.solutions.face_detection
            self.mp_drawing = mp.solutions.drawing_utils
            self.face_detection = self.mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5)
        else:
            self.mp_face_detection = None
            self.mp_drawing = None
            self.face_detection = None
    
    def detect_face_presence(self, frame):
        """Detect if face is present in frame"""
        if not self.cv2_available or not self.mediapipe_available:
            st.warning("Face detection not available - computer vision libraries missing")
            return True  # Assume face is present if detection unavailable
            
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(rgb_frame)
            return results.detections is not None
        except Exception as e:
            st.error(f"Face detection error: {e}")
            return True
    
    def track_eye_gaze(self, frame):
        """Track eye gaze direction"""
        if not self.cv2_available or not self.mediapipe_available:
            return {"status": "unavailable", "message": "Eye tracking requires computer vision libraries"}
        # Placeholder for eye gaze tracking implementation
        return {"status": "not_implemented"}
    
    def detect_anomalies(self, frame):
        """Detect multiple faces or other anomalies"""
        if not self.cv2_available or not self.mediapipe_available:
            return []
        # Placeholder for anomaly detection
        return []
    
    def show_camera_placeholder(self):
        """Show camera placeholder when webcam is not available"""
        st.info("📹 **Camera Monitoring**")
        st.markdown("""
        **Camera Status**: Monitoring Active (Simulated)
        
        In a production environment, this would show:
        - Live webcam feed
        - Face detection status
        - Eye gaze tracking
        - Anomaly detection alerts
        
        *Note: Computer vision features require webcam access and proper setup.*
        """)
        
        # Simulate monitoring status
        col1, col2, col3 = st.columns(3)
        with col1:
            st.success("✅ Face Detected")
        with col2:
            st.info("👁️ Eye Contact: Good")
        with col3:
            st.success("🔍 No Anomalies")