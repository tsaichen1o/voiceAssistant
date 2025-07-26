<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&display=swap');

* {
    font-family: 'Montserrat', sans-serif !important;
}

body, html {
    font-family: 'Montserrat', sans-serif !important;
    margin: 0;
    padding: 0;
}

.cover-page {
    min-height: 100vh;
    background: #ffffff;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    color: #2C3E50;
    padding: 20px;
    box-sizing: border-box;
}

.tum-logo {
    margin-bottom: 30px;
}

.report-title {
    font-size: 3.5em;
    font-weight: 800;
    margin-bottom: 20px;
    line-height: 1.2;
    color: #0e4378;
}

.report-subtitle {
    font-size: 1.8em;
    font-weight: 400;
    margin-bottom: 40px;
    opacity: 0.9;
    line-height: 1.4;
}

.report-sections {
    background: #f8f9fa;
    border-radius: 15px;
    padding: 30px;
    margin: 30px 0;
    border: 1px solid #e9ecef;
}

.report-sections h3 {
    font-size: 1.4em;
    font-weight: 600;
    margin-bottom: 15px;
    color: #0e4378;
}

.sections-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
    margin-top: 20px;
}

.section-item {
    background: #ffffff;
    padding: 15px;
    border-radius: 10px;
    border-left: 4px solid #0e4378;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.section-item h4 {
    margin: 0 0 5px 0;
    font-weight: 600;
    font-size: 1.1em;
}

.section-item p {
    margin: 0;
    opacity: 0.7;
    font-size: 0.9em;
    color: #2C3E50;
}

.team-section {
    background: #f8f9fa;
    border-radius: 15px;
    padding: 0 30px 30px 30px;
    margin: 30px 0;
    border: 1px solid #e9ecef;
}

.team-section h3 {
    font-size: 1.4em;
    font-weight: 600;
    margin-bottom: 20px;
    color: #0e4378;
}

.team-members {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
    margin-top: 20px;
}

.team-member {
    background: #ffffff;
    padding: 15px;
    border-radius: 10px;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.team-member h4 {
    margin: 0 0 5px 0;
    font-weight: 600;
    font-size: 1.0em;
}

.team-member p {
    margin: 0;
    opacity: 0.7;
    font-size: 0.85em;
    color: #2C3E50;
}

.project-info {
    margin-top: 40px;
    opacity: 0.9;
    color: #2C3E50;
}

.project-info p {
    margin: 8px 0;
    font-size: 1.1em;
}

.university-info {
    margin-top: 40px;
    padding-top: 10px;
    border-top: 1px solid #e9ecef;
    opacity: 0.8;
    color: #2C3E50;
}

.university-info h4 {
    font-size: 1.3em;
    font-weight: 600;
    margin-bottom: 10px;
}

.university-info p {
    margin: 5px 0;
    font-size: 1.0em;
}

@media (max-width: 768px) {
    .report-title {
        font-size: 2.5em;
    }
    
    .report-subtitle {
        font-size: 1.4em;
    }
    
    .sections-grid {
        grid-template-columns: 1fr;
    }
    
    .team-members {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 480px) {
    .team-members {
        grid-template-columns: 1fr;
    }
}
</style>

<div class="cover-page">
    <div class="tum-logo">
        <img src="tum_logo.svg" alt="TUM Logo" width="120" height="120">
    </div>
    <h1 class="report-title">go42TUM</h1>
    <h2 class="report-subtitle">A Real-Time Voice AI Consultant for TUM Applicants<br>Comprehensive Project Report</h2>
    <div class="team-section">
        <h3>Group 5</h3>
        <div class="team-members">
            <div class="team-member">
                <h4>Hao Lin</h4>
            </div>
            <div class="team-member">
                <h4>Han Hu</h4>
            </div>
            <div class="team-member">
                <h4>Rui Tang</h4>
            </div>
            <div class="team-member">
                <h4>TsaiChen Lo</h4>
            </div>
            <div class="team-member">
                <h4>Thi Bach Duong Bui</h4>
            </div>
            <div class="team-member">
                <h4>Zhihong Wu</h4>
            </div>
        </div>
    </div>
    <div class="university-info">
        <h4>Technical University of Munich (TUM)</h4>
        <p>School of Computation, Information and Technology</p>
        <p>[CITHN2014] Foundations and Application of Generative AI</p>
        <p>Summer Semester 2025</p>
        <p>27.07.2025</p>
    </div>
</div>

<div class="cover-page" style="min-height: 100vh; justify-content: flex-start; padding-top: 60px;">
    <div style="max-width: 800px; text-align: left; color: #2C3E50;">
        <h1 style="font-size: 2.0em; font-weight: 600; color: #2C3E50; text-align: left; margin-bottom: 30px; border-bottom: 2px solid #0e4378; padding-bottom: 15px;">
            Acknowledgments of Generative AI Usage
        </h1>
        <div style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #0e4378;">
            <p style="font-style: italic; color: #0e4378; font-weight: 500; margin: 0; font-size: 1.1em;">
                In accordance with the course policy on the use of Generative AI, this section details how our team utilized GenAI tools as an assistant in the creation of this project report and its accompanying documents.
            </p>
        </div>
        <p style="font-size: 1.0em; line-height: 1.6; margin-bottom: 20px;">
            Our approach was to leverage AI to enhance productivity and improve the quality of our work, while ensuring that all core concepts, analysis, and final decisions remained our own. The primary applications of GenAI in our workflow included:
        </p>
        <div style="margin: 25px 0;">
            <h3 style="font-family: 'Montserrat', sans-serif; font-weight: 600; color: #34495E; font-size: 1.2em; margin-bottom: 10px; border-bottom: 1px solid #BDC3C7; padding-bottom: 4px; display: block;">
                Conceptualization and Structuring
            </h3>
            <p style="font-size: 1.0em; line-height: 1.6; margin-left: 0;">
                During the initial phases, we used GenAI to brainstorm and generate foundational outlines for complex report sections, such as "System Design & Architecture" and "Methodology & Approach." This provided a solid starting point, which was then substantially expanded, detailed, and validated by the team's own expertise and research.
            </p>
        </div>
        <div style="margin: 25px 0;">
            <h3 style="font-family: 'Montserrat', sans-serif; font-weight: 600; color: #34495E; font-size: 1.2em; margin-bottom: 10px; border-bottom: 1px solid #BDC3C7; padding-bottom: 4px; display: block;">
                Language Refinement and Polishing
            </h3>
            <p style="font-size: 1.0em; line-height: 1.6; margin-left: 0;">
                Throughout the writing process, GenAI served as a sophisticated writing assistant. We employed it to paraphrase and shorten verbose sentences for better clarity, refine the professional and formal tone of the document, and ensure linguistic consistency across sections contributed by different team members.
            </p>
        </div>
        <div style="margin: 25px 0;">
            <h3 style="font-family: 'Montserrat', sans-serif; font-weight: 600; color: #34495E; font-size: 1.2em; margin-bottom: 10px; border-bottom: 1px solid #BDC3C7; padding-bottom: 4px; display: block;">
                Formatting and Content Generation
            </h3>
            <p style="font-size: 1.0em; line-height: 1.6; margin-left: 0;">
                GenAI was also used for several practical formatting tasks. This included generating clean Markdown for tables, assisting in the creation and structuring of the table of contents, and helping to design professional layouts for various report components.
            </p>
        </div>
        <div style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 25px 0; border-left: 4px solid #0e4378; text-align: center;">
            <p style="font-style: italic; color: #2C3E50; margin: 0; font-size: 0.95em;">
                <strong>Meta-Disclosure:</strong> This "Acknowledgments of Generative AI Usage" section itself was generated using GenAI tools and subsequently reviewed and approved by our team to ensure accuracy and completeness of our AI usage disclosure.
            </p>
        </div>
    </div>
</div>