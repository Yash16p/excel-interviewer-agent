import streamlit as st

def show_agreement_modal():
    """Show interview agreement modal using expandable section"""
    with st.expander("📋 Interview Instructions & Agreement", expanded=True):
        st.markdown("""
        ### 🎯 Interview Guidelines:
        - **This is a timed, adaptive mock interview** (text answers only)
        - **No external help allowed** - answers must be typed without assistance
        - **Tab switching is monitored** - a warning will appear if you switch tabs
        - **Questions adapt to your performance** - weaker candidates get more basic questions, stronger candidates move to advanced topics faster
        - **Time tracking** - your response time per question is recorded for recruiter insights
        - **Audio playback** - questions will be spoken automatically (browser may require first interaction)
        
        ### 📊 What We Measure:
        - **Technical Excel knowledge** across formulas, pivot tables, data cleaning, and productivity
        - **Problem-solving approach** and clarity of communication
        - **Response time** and consistency across questions
        - **Focus and attention** (tab switching behavior)
        
        ### ⚠️ Important:
        - Final feedback (scorecard + PDF report) is shown at the end
        - This assessment helps identify areas for improvement
        - **Tech note:** If audio doesn't autoplay, click on the page once to enable audio playback
        """)
        
        st.markdown("---")
        st.markdown("**By proceeding, you agree to follow these interview rules and understand that your responses and timing will be recorded.**")

def format_duration(seconds):
    """Format seconds into human readable duration"""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
