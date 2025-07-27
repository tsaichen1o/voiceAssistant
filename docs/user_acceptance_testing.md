<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&display=swap');

* {
    font-family: 'Montserrat', sans-serif !important;
}

body, html {
    font-family: 'Montserrat', sans-serif !important;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 600;
}

p, span, div, li, td, th, blockquote, pre {
    font-family: 'Montserrat', sans-serif !important;
}

code {
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
    color: green;
    background-color: #f8f9fa;
    padding: 2px 4px;
    border-radius: 3px;
}

a, a:hover, a:visited {
    font-family: 'Montserrat', sans-serif !important;
}

strong, b, em, i {
    font-family: 'Montserrat', sans-serif !important;
}

ul, ol, dl {
    font-family: 'Montserrat', sans-serif !important;
}

table {
    font-family: 'Montserrat', sans-serif !important;
}

input, textarea, select, button {
    font-family: 'Montserrat', sans-serif !important;
}
</style>


<img src="pics/tum_logo.svg" alt="TUM Logo" width="60" align="right">

<div style="font-family: 'Montserrat', sans-serif;">

# **User Acceptance Testing**
> A Real-Time Voice AI Consultant for TUM Applicants

<div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #0e4378; margin: 20px 0;">
<strong>Group:</strong> 5  <br/>
<strong>Live Demo:</strong> <a href="https://voice-assistant-gilt.vercel.app/">https://voice-assistant-gilt.vercel.app/</a> <br/>
<strong>GitHub Repository:</strong> <a href="https://github.com/tsaichen1o/voiceAssistant">https://github.com/tsaichen1o/voiceAssistant</a>
</div>

<span style="border-bottom: 1px solid #BDC3C7;display: block;"></span>

1. **[User Case Study](#user-case-study)** <br/>
    [1.1 Process Overview](#process-overview) <br/>
    [1.2 Advantages](#advantages) <br/>
    [1.3 Limitations](#limitations) <br/>
2. **[UAT Design and Execution](#uat-design-and-execution)** <br/>
    [2.1 Gemini Evaluation (Live Interaction)](#gemini-evaluation-live-interaction) <br/>
    [2.2 Speech Framework Evaluation (Video + Questionnaire)](#speech-framework-evaluation-video--questionnaire) <br/>
3. **[Summary and Insights](#summary-and-insights)** <br/>
    [3.1 Improvement Suggestions](#improvement-suggestions) <br/>
    [3.2 Conclusion](#conclusion) <br/>
**[Appendix](#appendix)** <br/>
    [Figure A1: Gemini Feedback Bar Plot](#figure-a1-gemini-feedback-bar-plot) <br/>
    [Figure A2: AHP Result Summary](#figure-a2-ahp-result-summary) <br/>

<span style="border-bottom: 1px solid #BDC3C7;display: block;"></span>

<div style="page-break-after: always; visibility: hidden"> 
\pagebreak 
</div>

This report presents a comprehensive evaluation of the user acceptance of our AI voice assistant system. The system is built on the Gemini large language model and integrates three different voice processing frameworks: **SpeechBrain**, **Whisper + Coqui TTS**, and **Whisper + Edge TTS**. It supports **English and German voice input only** and is tailored to assist international students applying to TUM.

To ensure structured and meaningful user engagement, the User Acceptance Testing (UAT) report was split into two complementary streams:
1. Real-time feedback on Gemini's performance in understanding and answering user queries;
2. Analytical evaluation of three speech processing frameworks through video demonstrations and multi-dimensional scoring.

---

## <span id="user-case-study" style="font-family: 'Montserrat', sans-serif; font-weight: 600; color: #2C3E50; border-bottom: 2px solid #0e4378; padding-bottom: 8px; display: block;">1. User Case Study</span>

**Participant Profile**  
The selected user, **Zhihong Wu**, is a 23-year-old prospective student from China preparing to apply to TUM for a Master’s program in Informatics. He is fluent in English and has intermediate German skills. He represents a typical international applicant who relies on online resources and voice assistants for navigating the complex university application process.

### <span id="process-overview" style="font-family: 'Montserrat', sans-serif; font-weight: 600; color: #34495E; border-bottom: 1px solid #BDC3C7; padding-bottom: 4px; display: block;">1.1 Process Overview</span>

- Zhihong was first introduced to the purpose of the assistant and received a link to the Gemini-powered voice platform.
- He used the assistant to ask questions about TUM’s deadlines, required documents, and admission criteria in both English and German.
- Afterwards, he watched three short demo videos showcasing different speech frameworks (SpeechBrain, Whisper + Coqui, Whisper + Edge) handling the same input query.
- He completed two separate questionnaires: one for Gemini interaction, and one for speech framework evaluation.

### <span id="advantages" style="font-family: 'Montserrat', sans-serif; font-weight: 600; color: #34495E; border-bottom: 1px solid #BDC3C7; padding-bottom: 4px; display: block;">1.2 Advantages</span>

- Found the assistant easy to use and fast in processing  
- The bilingual capability was helpful for trying both English and German  
- Appreciated the clear pronunciation in the Whisper + Coqui output

### <span id="limitations" style="font-family: 'Montserrat', sans-serif; font-weight: 600; color: #34495E; border-bottom: 1px solid #BDC3C7; padding-bottom: 4px; display: block;">1.3 Limitations</span>

- Answers were sometimes too short and not sufficiently informative  
- When trying a few test phrases in Italian, the assistant failed to respond  
- Long interactions could cause the system to hang

For detailed user feedback metrics, please see [Figure A1: Gemini Feedback Bar Plot](#figure-a1-gemini-feedback-bar-plot) in the Appendix.


## <span id="uat-design-and-execution" style="font-family: 'Montserrat', sans-serif; font-weight: 600; color: #2C3E50; border-bottom: 2px solid #0e4378; padding-bottom: 8px; display: block;">2. UAT Design and Execution</span>

The UAT plan was designed to evaluate:

- The effectiveness of Gemini in answering application-related questions  
- The accuracy and smoothness of speech recognition and synthesis for both English and German  
- The comparative performance of the three voice processing frameworks  

### <span id="gemini-evaluation-live-interaction" style="font-family: 'Montserrat', sans-serif; font-weight: 600; color: #34495E; border-bottom: 1px solid #BDC3C7; padding-bottom: 4px; display: block;">2.1 Gemini Evaluation (Live Interaction)</span> 

Participants were given a web link to interact directly with the AI voice assistant powered by Gemini. They were asked to speak English or German questions related to TUM applications, such as:

- “What is the deadline for TUM master’s application?”  
- “Welche Unterlagen brauche ich für die Bewerbung?”

After using the system, they filled out an online survey rating:

- Response accuracy  
- Language understanding  
- Interaction speed  
- Overall satisfaction  

**Sample User Feedback (Gemini):**
-  The answers are generally satisfying  
-  Recognition is fast and accurate  
-  Not much information given sometimes  
-  Doesn’t respond if language is not English or German

### <span id="speech-framework-evaluation-video--questionnaire" style="font-family: 'Montserrat', sans-serif; font-weight: 600; color: #34495E; border-bottom: 1px solid #BDC3C7; padding-bottom: 4px; display: block;">2.2 Speech Framework Evaluation (Video + Questionnaire)</span>

To ensure consistency in input and eliminate bias caused by live variation, participants were shown pre-recorded videos demonstrating the performance of the three speech frameworks. Each video showed how the same query was processed via:

- **SpeechBrain**  
- **Whisper + Coqui TTS**  
- **Whisper + Edge TTS**

Participants completed a detailed questionnaire evaluating each framework based on:

- Voice recognition accuracy  
- Response latency  
- Naturalness of synthesized voice  
- Overall usability  

In addition to subjective ratings, we also included system-measured metrics:

- **ASR word error rate (WER)**  
- **Average response time per framework**

These subjective and objective factors were combined using the **Analytic Hierarchy Process (AHP)** to compute a final score and ranking. For the complete AHP analysis results, please see [Figure A2: AHP Result Summary](#figure-a2-ahp-result-summary) in the Appendix.

---
## <span id="summary-and-insights" style="font-family: 'Montserrat', sans-serif; font-weight: 600; color: #2C3E50; border-bottom: 2px solid #0e4378; padding-bottom: 8px; display: block;">3. Summary and Insights</span>

The UAT revealed several important insights:

- Gemini’s understanding and language handling were rated positively, though users wished for more detailed answers  
- Speech recognition worked well in both English and German, with minor latency noted in SpeechBrain  
- Whisper + Coqui TTS ranked highest overall in AHP analysis, balancing speed, clarity, and reliability  

### <span id="improvement-suggestions" style="font-family: 'Montserrat', sans-serif; font-weight: 600; color: #34495E; border-bottom: 1px solid #BDC3C7; padding-bottom: 4px; display: block;">3.1 Improvement Suggestions</span>

- Expand the assistant’s answer base for more informative replies  
- Improve stability during longer sessions  
- Add prompts or fallback responses when unsupported languages are used  
- Consider multilingual expansion beyond English and German in future versions  


### <span id="conclusion" style="font-family: 'Montserrat', sans-serif; font-weight: 600; color: #34495E; border-bottom: 1px solid #BDC3C7; padding-bottom: 4px; display: block;">3.2 Conclusion</span>
The UAT provided valuable user-centric insights into both the AI and speech components of the system. The testing plan not only validated our core functionalities but also surfaced actionable improvements. It demonstrated that the system is well-received by its target audience and ready for future iteration based on concrete feedback.

<div style="page-break-after: always; visibility: hidden"> 
\pagebreak 
</div>

## <span id="appendix" style="font-family: 'Montserrat', sans-serif; font-weight: 600; color: #2C3E50; border-bottom: 2px solid #0e4378; padding-bottom: 8px; display: block;">Appendix</span>

### <span id="figure-a1-gemini-feedback-bar-plot" style="font-family: 'Montserrat', sans-serif; font-weight: 600; color: #34495E; border-bottom: 1px solid #BDC3C7; padding-bottom: 4px; display: block;">Figure A1: Gemini Feedback Bar Plot</span>

<div style="text-align: center;">
<img src="pics/UAT1.png" alt="Gemini Feedback Bar Plot" style="width: 75%;">
</div>

**Figure A1:** Bar plot visualization showing user feedback ratings for Gemini's performance across different evaluation criteria such as response accuracy and interaction speed.

### <span id="figure-a2-ahp-result-summary" style="font-family: 'Montserrat', sans-serif; font-weight: 600; color: #34495E; border-bottom: 1px solid #BDC3C7; padding-bottom: 4px; display: block;">Figure A2: AHP Result Summary</span>

<div style="text-align: center;">
<img src="pics/UAT2.png" alt="AHP Result Summary" style="width: 75%;">
</div>

**Figure A2:** Comprehensive AHP analysis results showing the final ranking and scoring of the three speech frameworks (SpeechBrain, Whisper + Coqui TTS, and Whisper + Edge TTS) based on combined subjective user ratings and objective performance metrics.
</div>