import streamlit as st
import time
import requests
from datetime import datetime

class TabMonitor:
    def __init__(self, session_id=None, backend_url="http://localhost:8000"):
        self.tab_switches = 0
        self.last_focus_time = time.time()
        self.session_id = session_id
        self.backend_url = backend_url
        self.warning_count = 0
        self.max_warnings = 3
    
    def initialize_tab_monitoring(self):
        """Initialize JavaScript-based tab monitoring"""
        tab_monitor_js = """
        <script>
        let tabSwitchCount = 0;
        let isTabActive = true;
        
        // Track tab visibility changes
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                isTabActive = false;
                tabSwitchCount++;
                
                // Send warning to Streamlit
                window.parent.postMessage({
                    type: 'tab_switch',
                    count: tabSwitchCount,
                    timestamp: new Date().toISOString()
                }, '*');
                
                // Show warning
                alert('⚠️ WARNING: Tab switching detected! This has been logged. Warning ' + 
                      (tabSwitchCount) + ' of 3. Excessive tab switching may affect your evaluation.');
            } else {
                isTabActive = true;
            }
        });
        
        // Track window focus changes
        window.addEventListener('blur', function() {
            if (isTabActive) {
                tabSwitchCount++;
                window.parent.postMessage({
                    type: 'window_blur',
                    count: tabSwitchCount,
                    timestamp: new Date().toISOString()
                }, '*');
            }
        });
        
        // Prevent right-click context menu
        document.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            alert('⚠️ Right-click is disabled during the interview.');
        });
        
        // Detect developer tools (basic detection)
        let devtools = {open: false, orientation: null};
        setInterval(function() {
            if (window.outerHeight - window.innerHeight > 200 || 
                window.outerWidth - window.innerWidth > 200) {
                if (!devtools.open) {
                    devtools.open = true;
                    window.parent.postMessage({
                        type: 'devtools_detected',
                        timestamp: new Date().toISOString()
                    }, '*');
                    alert('⚠️ WARNING: Developer tools detected! This has been logged.');
                }
            } else {
                devtools.open = false;
            }
        }, 1000);
        </script>
        """
        
        st.components.v1.html(tab_monitor_js, height=0)
    
    def handle_tab_switch_event(self, event_data):
        """Handle tab switch event and show warning"""
        self.tab_switches += 1
        self.warning_count += 1
        
        # Log to database
        self.log_proctoring_event("tab_switch", datetime.now(), {
            "switch_count": self.tab_switches,
            "warning_number": self.warning_count
        })
        
        # Show warning in Streamlit
        if self.warning_count <= self.max_warnings:
            st.error(f"⚠️ **WARNING {self.warning_count}/{self.max_warnings}**: Tab switching detected! "
                    f"This behavior is being monitored and logged.")
            
            if self.warning_count == self.max_warnings:
                st.error("🚨 **FINAL WARNING**: Maximum tab switches reached. "
                        "Further violations may result in interview termination.")
        else:
            st.error("🚨 **INTERVIEW VIOLATION**: Excessive tab switching detected. "
                    "Your interview may be flagged for review.")
        
        return self.warning_count >= self.max_warnings
    
    def show_proctoring_rules(self):
        """Display proctoring rules to candidate"""
        st.sidebar.markdown("### 📋 Interview Guidelines")
        st.sidebar.warning("""
        **Please follow these rules:**
        
        ✅ Stay on this tab during the interview
        ✅ Keep your face visible to the camera
        ✅ Speak clearly into the microphone
        ✅ Maintain eye contact with the camera
        
        ❌ Do not switch tabs or windows
        ❌ Do not use external resources
        ❌ Do not have multiple people present
        ❌ Do not use developer tools
        
        **Violations will be logged and may affect your evaluation.**
        """)
        
        # Show current violation count
        if self.warning_count > 0:
            st.sidebar.error(f"⚠️ Warnings: {self.warning_count}/{self.max_warnings}")
    
    def log_proctoring_event(self, event_type, timestamp, details=None):
        """Log proctoring events to database via backend API"""
        if not self.session_id:
            return None
            
        event_data = {
            "session_id": self.session_id,
            "event_type": event_type,
            "timestamp": timestamp.isoformat(),
            "severity": self._get_severity(event_type),
            "details": details or {}
        }
        
        try:
            response = requests.post(
                f"{self.backend_url}/log-proctoring-event",
                json=event_data,
                timeout=5
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            st.error(f"Failed to log proctoring event: {e}")
            return None
    
    def get_violation_summary(self):
        """Get summary of all violations for this session"""
        return {
            "total_tab_switches": self.tab_switches,
            "warning_count": self.warning_count,
            "max_warnings_exceeded": self.warning_count > self.max_warnings,
            "violation_severity": "high" if self.warning_count > self.max_warnings else 
                                "medium" if self.warning_count > 1 else "low"
        }
    
    def _get_severity(self, event_type):
        """Determine severity level of proctoring event"""
        severity_map = {
            "tab_switch": "medium",
            "window_blur": "medium", 
            "devtools_detected": "high",
            "multiple_faces": "high",
            "no_face_detected": "high",
            "audio_anomaly": "medium",
            "right_click_attempt": "low"
        }
        return severity_map.get(event_type, "low")
    
    def reset_monitoring(self):
        """Reset monitoring counters for new session"""
        self.tab_switches = 0
        self.warning_count = 0
        self.last_focus_time = time.time()