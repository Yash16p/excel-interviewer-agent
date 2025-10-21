from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
import matplotlib.pyplot as plt
import io
import base64
from typing import Dict, List
from datetime import datetime

class PDFReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.custom_styles = self._create_custom_styles()
    
    def create_report(self, session_data: Dict) -> str:
        """Generate comprehensive interview report PDF"""
        filename = f"interview_report_{session_data.get('candidate_name', 'candidate')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        doc = SimpleDocTemplate(filename, pagesize=A4)
        story = []
        
        # Header
        story.extend(self._create_header(session_data))
        
        # Executive Summary
        story.extend(self._create_executive_summary(session_data))
        
        # Detailed Scores
        story.extend(self._create_detailed_scores(session_data))
        
        # Performance Charts
        story.extend(self._create_performance_charts(session_data))
        
        # Interview Analysis
        story.extend(self._create_interview_analysis(session_data))
        
        # Proctoring Report
        story.extend(self._create_proctoring_report(session_data))
        
        # Recommendations
        story.extend(self._create_recommendations(session_data))
        
        # Build PDF
        doc.build(story)
        return filename
    
    def _create_custom_styles(self) -> Dict:
        """Create custom paragraph styles"""
        return {
            'CustomTitle': ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.darkblue,
                alignment=1  # Center alignment
            ),
            'SectionHeader': ParagraphStyle(
                'SectionHeader',
                parent=self.styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.darkblue,
                borderWidth=1,
                borderColor=colors.darkblue,
                borderPadding=5
            ),
            'ScoreText': ParagraphStyle(
                'ScoreText',
                parent=self.styles['Normal'],
                fontSize=12,
                spaceAfter=6
            )
        }
    
    def _create_header(self, session_data: Dict) -> List:
        """Create report header section"""
        elements = []
        
        # Title
        title = Paragraph("AI Interview Assessment Report", self.custom_styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Candidate info table
        candidate_info = [
            ['Candidate:', session_data.get('candidate_name', 'N/A')],
            ['Role:', session_data.get('interview_role', 'N/A')],
            ['Date:', session_data.get('interview_date', datetime.now().strftime('%Y-%m-%d'))],
            ['Duration:', f"{session_data.get('duration_minutes', 0)} minutes"],
            ['Overall Score:', f"{session_data.get('overall_score', 0):.1f}/10"]
        ]
        
        table = Table(candidate_info, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, -1), (1, -1), colors.lightgreen if session_data.get('overall_score', 0) >= 7 else colors.lightyellow),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 30))
        
        return elements
    
    def _create_executive_summary(self, session_data: Dict) -> List:
        """Create executive summary section"""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.custom_styles['SectionHeader']))
        
        summary_text = session_data.get('executive_summary', 
            "The candidate demonstrated solid technical knowledge with room for improvement in communication clarity.")
        
        elements.append(Paragraph(summary_text, self.styles['Normal']))
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_detailed_scores(self, session_data: Dict) -> List:
        """Create detailed scoring section"""
        elements = []
        
        elements.append(Paragraph("Detailed Assessment Scores", self.custom_styles['SectionHeader']))
        
        scores = session_data.get('detailed_scores', {
            'Technical Knowledge': 8.5,
            'Communication Skills': 7.8,
            'Problem Solving': 8.2,
            'Confidence Level': 7.5,
            'Clarity of Expression': 7.9
        })
        
        score_data = [['Assessment Category', 'Score (1-10)', 'Rating']]
        for category, score in scores.items():
            rating = self._get_rating_text(score)
            score_data.append([category, f"{score:.1f}", rating])
        
        score_table = Table(score_data, colWidths=[2.5*inch, 1*inch, 1.5*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(score_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_performance_charts(self, session_data: Dict) -> List:
        """Create performance visualization charts"""
        elements = []
        
        elements.append(Paragraph("Performance Visualization", self.custom_styles['SectionHeader']))
        
        # Create a simple bar chart using matplotlib
        scores = session_data.get('detailed_scores', {})
        if scores:
            chart_buffer = self._generate_score_chart(scores)
            if chart_buffer:
                elements.append(Image(chart_buffer, width=5*inch, height=3*inch))
        
        elements.append(Spacer(1, 20))
        return elements
    
    def _create_interview_analysis(self, session_data: Dict) -> List:
        """Create interview analysis section"""
        elements = []
        
        elements.append(Paragraph("Interview Analysis", self.custom_styles['SectionHeader']))
        
        # Strengths
        elements.append(Paragraph("Strengths:", self.styles['Heading3']))
        strengths = session_data.get('strengths', ['Technical competency', 'Problem-solving approach'])
        for strength in strengths:
            elements.append(Paragraph(f"• {strength}", self.styles['Normal']))
        
        elements.append(Spacer(1, 10))
        
        # Areas for Improvement
        elements.append(Paragraph("Areas for Improvement:", self.styles['Heading3']))
        improvements = session_data.get('improvements', ['Communication clarity', 'Reduce filler words'])
        for improvement in improvements:
            elements.append(Paragraph(f"• {improvement}", self.styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_proctoring_report(self, session_data: Dict) -> List:
        """Create proctoring analysis section"""
        elements = []
        
        elements.append(Paragraph("Proctoring Analysis", self.custom_styles['SectionHeader']))
        
        proctoring_data = session_data.get('proctoring_events', [])
        
        if proctoring_data:
            event_table_data = [['Event Type', 'Count', 'Severity']]
            event_summary = {}
            
            for event in proctoring_data:
                event_type = event.get('event_type', 'unknown')
                severity = event.get('severity', 'low')
                
                if event_type not in event_summary:
                    event_summary[event_type] = {'count': 0, 'severity': severity}
                event_summary[event_type]['count'] += 1
            
            for event_type, data in event_summary.items():
                event_table_data.append([
                    event_type.replace('_', ' ').title(),
                    str(data['count']),
                    data['severity'].title()
                ])
            
            proctoring_table = Table(event_table_data, colWidths=[2*inch, 1*inch, 1*inch])
            proctoring_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(proctoring_table)
        else:
            elements.append(Paragraph("No proctoring violations detected.", self.styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_recommendations(self, session_data: Dict) -> List:
        """Create recommendations section"""
        elements = []
        
        elements.append(Paragraph("Hiring Recommendation", self.custom_styles['SectionHeader']))
        
        overall_score = session_data.get('overall_score', 0)
        recommendation = self._get_hiring_recommendation(overall_score)
        
        elements.append(Paragraph(f"Recommendation: {recommendation}", self.styles['Normal']))
        elements.append(Spacer(1, 10))
        
        rationale = session_data.get('recommendation_rationale', 
            "Based on technical competency and communication skills demonstrated during the interview.")
        elements.append(Paragraph(f"Rationale: {rationale}", self.styles['Normal']))
        
        return elements
    
    def _generate_score_chart(self, scores: Dict) -> io.BytesIO:
        """Generate score visualization chart"""
        try:
            fig, ax = plt.subplots(figsize=(8, 5))
            
            categories = list(scores.keys())
            values = list(scores.values())
            
            bars = ax.bar(categories, values, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])
            ax.set_ylabel('Score')
            ax.set_title('Interview Assessment Scores')
            ax.set_ylim(0, 10)
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{value:.1f}', ha='center', va='bottom')
            
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # Save to buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plt.close()
            
            return buffer
        except Exception as e:
            print(f"Chart generation error: {e}")
            return None
    
    def _get_rating_text(self, score: float) -> str:
        """Convert numeric score to rating text"""
        if score >= 9:
            return "Excellent"
        elif score >= 8:
            return "Very Good"
        elif score >= 7:
            return "Good"
        elif score >= 6:
            return "Satisfactory"
        elif score >= 5:
            return "Needs Improvement"
        else:
            return "Poor"
    
    def _get_hiring_recommendation(self, overall_score: float) -> str:
        """Generate hiring recommendation based on score"""
        if overall_score >= 8.5:
            return "Strong Hire"
        elif overall_score >= 7.5:
            return "Hire"
        elif overall_score >= 6.5:
            return "Weak Hire"
        elif overall_score >= 5.5:
            return "No Hire - Consider for Different Role"
        else:
            return "No Hire"