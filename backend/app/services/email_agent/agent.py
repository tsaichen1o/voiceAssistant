from google.adk.agents import Agent
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings


def send_email(user_email: str, recipient_email: str, user_question: str):
    """Send an email to human staff who is most related to user question
    Args:
        user_email (str): the email address of user
        recipient_email (str): the email address of the human staff (whom this email is sent to)
        user_question (str): a brief summary of the conversation (contain all important information) and the user questions that need staff helps
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.EMAIL_ADDRESS
        msg['To'] = recipient_email
        msg['Subject'] = "[URGENT] unexpected question"
        body = f"Dear Sir/Madam,\n\nThe LLM could not answer the question: '{user_question}'. When you have the answer, please send email to user: {user_email}"

        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_ADDRESS, settings.EMAIL_PASSWORD)
            server.sendmail(settings.EMAIL_ADDRESS, recipient_email, msg.as_string())

        return {
            "status": "success",
            "report": ("The email was sent successfully.")
        }
    except Exception as e:
        print(f"Error sending email: {e}.")
        return {
            "status": "error",
            "error_message": f"Failed to send email. Encountered this error: {e}"
        }


email_agent = Agent(
    name="email_agent",
    model=settings.GEMINI_MODEL,
    description=(
        "Agent to ask for user email and send an email to the human staff to answer user difficult question later"
    ),
    instruction=(
        "You are a helpful agent who will be triggered when the base agent "
        "cannot answer user question and need to email human staff. You first "
        "ask for user email address for the staff to contact later, then you "
        "choose the staff that works on the area that most related to the "
        "who you believe can answer the question. The staffs and their email " \
        "addresses are shown in here." \
        "TsaiChen Lo (responsible for tuition fees related topics): junidev5@gmail.com " \
        "Duong Bui (responsible for application submission related topics): junidev5@gmail.com" \
        "Rui Tang (responsible for advising which program to select): junidev5@gmail.com" \
        "Zhihong Wu (responsible for programs related information): junidev5@gmail.com" \
        ""
    ),
    tools=[send_email],
)
