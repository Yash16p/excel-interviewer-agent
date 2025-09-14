# 🧑‍💻 AI-Powered Excel Mock Interviewer

A sophisticated AI-driven interview system that conducts realistic Excel skill assessments using advanced language models. This application simulates a professional interview experience with intelligent question generation, comprehensive answer evaluation, and detailed feedback reporting.

## ✨ Features

### 🎯 Core Capabilities
- **Intelligent Interview Flow**: Multi-turn conversation with adaptive questioning
- **AI-Powered Evaluation**: Sophisticated answer assessment using GPT-4o-mini
- **Smart Follow-up Logic**: Contextual follow-up questions (max 2 per interview)
- **Text-to-Speech Integration**: Audio playback for all questions and feedback
- **Professional PDF Reports**: Comprehensive performance summaries
- **Session State Management**: Maintains conversation context throughout

### 🎪 Interview Experience
- **4 Main Questions**: Exactly 4 core Excel questions per interview
- **Adaptive Difficulty**: Questions adjust based on candidate performance
- **No Immediate Feedback**: Clean interview experience without score spoilers
- **Professional Tone**: Neutral, interviewer-like evaluation style
- **Skill Area Coverage**: Formulas, Pivot Tables, Data Cleaning, Productivity

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd excel-interviewer-agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

6. **Access the application**
   Open your browser to `http://localhost:8501`

## 🏗️ Architecture

### File Structure
```
excel-interviewer-agent/
├── app.py              # Main Streamlit application
├── utils.py            # Core AI functionality and utilities
├── questions.py        # Interview configuration and constants
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (create this)
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

### Core Components

#### 📱 `app.py` - User Interface
- **Session State Management**: Tracks interview progress, transcript, and scores
- **Interview Flow Control**: Manages question progression and follow-up logic
- **UI Components**: Streamlit interface with audio integration
- **Report Generation**: Displays results and handles PDF downloads

#### 🤖 `utils.py` - AI Engine
- **Answer Evaluation** (`evaluate_with_llm`): Multi-dimensional scoring system
- **Question Generation** (`select_next_question_api`): Dynamic question creation
- **Text-to-Speech** (`text_to_speech`): Audio generation for accessibility
- **PDF Reports** (`generate_pdf_report`): Professional feedback documents
- **Memory Management** (`get_langchain_memory`): Conversation context tracking

#### ⚙️ `questions.py` - Configuration
- **Skill Areas**: Defines Excel competency categories
- **Interview Length**: Controls question count (4 questions)
- **Fallback Questions**: Backup questions for API failures

## 🎮 How It Works

### Interview Process

1. **Introduction**
   - AI introduces itself with audio
   - Candidate enters name (optional)
   - Interview begins with first question

2. **Question Flow**
   - 4 main questions covering different Excel skill areas
   - Each question includes audio playback
   - Adaptive difficulty based on performance
   - Smart follow-up questions (3-4/5 scores only, max 2 total)

3. **Answer Evaluation**
   - Multi-dimensional scoring (Correctness, Efficiency, Clarity, Completeness)
   - Professional, neutral feedback tone
   - No immediate score display during interview

4. **Results & Reporting**
   - Overall score calculation
   - Skill area breakdown
   - Complete transcript with individual feedback
   - Downloadable PDF report

### AI Evaluation System

The system uses a sophisticated evaluation approach:

```python
{
  "score": <int 1-5>,
  "breakdown": {
    "Correctness": <int 1-5>,
    "Efficiency": <int 1-5>, 
    "Clarity": <int 1-5>,
    "Completeness": <int 1-5>
  },
  "feedback": "<professional feedback>",
  "followup": "<optional follow-up question>"
}
```

### Follow-up Logic
- **No follow-up**: Perfect scores (5/5) or very low scores (1-2/5)
- **Follow-up asked**: Medium scores (3-4/5) with room for improvement
- **Maximum**: 2 follow-up questions per interview
- **Smart termination**: Ends after exactly 4 main questions

## 🛠️ Technical Details

### Dependencies
- **streamlit**: Web application framework
- **openai**: GPT-4o-mini integration for AI evaluation
- **langchain**: Memory management for conversation context
- **reportlab**: PDF report generation
- **gTTS**: Text-to-speech functionality
- **python-dotenv**: Environment variable management

### AI Model Configuration
- **Model**: GPT-4o-mini (cost-efficient)
- **Temperature**: 0.0 for evaluation (consistent), 0.7 for question generation (creative)
- **Max Tokens**: 350 for evaluation, 400 for question generation

### Security & Privacy
- API keys stored in environment variables
- `.gitignore` excludes sensitive files
- No data persistence beyond session

## 📊 Performance Metrics

### Evaluation Criteria
1. **Correctness**: Technical accuracy of the answer
2. **Efficiency**: Optimal approach and methodology
3. **Clarity**: Communication and explanation quality
4. **Completeness**: Thoroughness of the response

### Skill Areas Covered
- **Formulas & Functions**: Basic to advanced Excel functions
- **Pivot Tables**: Data summarization and analysis
- **Data Cleaning**: Data preparation and manipulation
- **Productivity/Protection**: Workflow optimization and security

## 🎯 Use Cases

### Educational
- **Student Assessment**: Evaluate Excel skills for courses
- **Skill Verification**: Validate Excel competency levels
- **Practice Interviews**: Mock interview preparation

### Professional
- **Hiring Process**: Screen candidates for Excel roles
- **Training Assessment**: Measure training effectiveness
- **Skill Gap Analysis**: Identify areas for improvement

## 🔧 Configuration

### Customizing Questions
Edit `questions.py` to modify:
- Interview length (MIN_QUESTIONS, MAX_QUESTIONS)
- Skill areas covered (SKILL_AREAS)
- Fallback questions (FALLBACK_QUESTIONS)

### Adjusting Evaluation
Modify the evaluation prompt in `utils.py`:
- Scoring criteria
- Feedback tone
- Follow-up triggers

## 🐛 Troubleshooting

### Common Issues

1. **API Key Error**
   ```
   EnvironmentError: Set OPENAI_API_KEY in your .env file
   ```
   **Solution**: Create `.env` file with valid OpenAI API key

2. **Import Errors**
   ```
   ImportError: cannot import name 'select_next_question_api'
   ```
   **Solution**: Ensure all dependencies are installed with `pip install -r requirements.txt`

3. **Audio Playback Issues**
   - Check internet connection for gTTS
   - Verify temp directory permissions

### Performance Tips
- Use stable internet connection for API calls
- Close other applications to free up memory
- Restart browser if Streamlit becomes unresponsive

## 📈 Future Enhancements

### Planned Features
- **Multiple Difficulty Levels**: Beginner, Intermediate, Advanced tracks
- **Custom Question Sets**: Industry-specific Excel assessments
- **Analytics Dashboard**: Performance tracking over time
- **Multi-language Support**: Localized interviews
- **Integration APIs**: Connect with HR systems

### Technical Improvements
- **Caching**: Reduce API calls for repeated questions
- **Offline Mode**: Local question bank for reliability
- **Advanced Analytics**: Detailed performance insights
- **Mobile Optimization**: Responsive design improvements

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For support, questions, or feature requests:
- Create an issue in the repository
- Contact the development team
- Check the troubleshooting section above

---

**Built with ❤️ using Streamlit, OpenAI, and modern AI technologies**
