import streamlit as st

def show_instructions_modal():
    """Show interview instructions in an expandable section instead of modal"""
    with st.expander("📋 Interview Instructions", expanded=False):
        st.markdown("""
        ### Interview Guidelines:
        - This is a timed, adaptive mock interview (text answers)
        - The interviewer will speak each question automatically (browser may require first interaction)
        - Do not switch tabs or try to navigate away — a warning will appear
        - Final feedback (scorecard + PDF) is shown at the end
        - **Tech note:** If audio doesn't autoplay, click on the page once to enable audio playback
        """)

def tab_detection_component(tab_change_count):
    """Generate JavaScript component for tab change detection"""
    return f"""
    <script>
    let tabChangeCount = {tab_change_count};
    document.addEventListener('visibilitychange', function() {{
        if (document.hidden && !window.interviewComplete) {{
            tabChangeCount++;
            alert("Attention: You switched tabs or minimized the window. Please return to the interview. This event may be recorded by the interviewer. Tab changes: " + tabChangeCount);
            // Update the hidden input
            const input = document.querySelector('input[type="number"]');
            if (input) {{
                input.value = tabChangeCount;
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
        }}
    }});
    window.addEventListener('blur', function() {{
        if (!document.hidden && !window.interviewComplete) {{
            // Handle blur events if needed
        }}
    }});
    </script>
    """