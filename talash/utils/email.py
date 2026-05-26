"""
Email utility for sending recommendation emails to candidates.
Uses SMTP configured via environment variables.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("EMAIL_USER")
SMTP_PASSWORD = os.getenv("EMAIL_PASSWORD")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", SMTP_USERNAME)
SENDER_NAME = os.getenv("SENDER_NAME", "TALASH System")


def send_email(to_email: str, subject: str, html_body: str) -> dict:
    """
    Send an HTML email via SMTP.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_body: HTML email body content

    Returns:
        {"success": True} on success
        {"success": False, "error": "..."} on failure
    """
    try:
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            return {
                "success": False,
                "error": "SMTP credentials not configured in environment variables"
            }

        if not to_email:
            return {
                "success": False,
                "error": "Recipient email address is required"
            }

        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        message["To"] = to_email

        # Attach HTML body
        html_part = MIMEText(html_body, "html")
        message.attach(html_part)

        # Send via SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, message.as_string())

        return {"success": True}

    except smtplib.SMTPException as e:
        return {
            "success": False,
            "error": f"SMTP error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to send email: {str(e)}"
        }


def build_recommendation_email_html(
    candidate_name: str,
    overall_score: float,
    overall_grade: str,
    recommendations: list,
    summary_interpretation: str
) -> str:
    """
    Build an HTML email body with CV evaluation recommendations.

    Args:
        candidate_name: Name of the candidate
        overall_score: Overall CV score (0-100)
        overall_grade: Overall grade (EXCELLENT, GOOD, SATISFACTORY, WEAK)
        recommendations: List of recommendation strings
        summary_interpretation: Summary interpretation text

    Returns:
        HTML string for email body
    """
    recommendations_section = ""
    recommendations_html = ""
    if recommendations:
        recommendations_html = "<ol style='margin: 15px 0; padding-left: 25px;'>"
        for i, rec in enumerate(recommendations, 1):
            recommendations_html += f"<li style='margin-bottom: 10px; line-height: 1.5;'>{rec}</li>"
        recommendations_html += "</ol>"
        recommendations_section = (
            '<div class="section">'
            '<h2 class="section-title">💡 Recommendations for Improvement</h2>'
            f"{recommendations_html}"
            "</div>"
        )

    grade_color = {
        "EXCELLENT": "#00e5cc",
        "GOOD": "#10b981",
        "SATISFACTORY": "#f59e0b",
        "WEAK": "#ef4444"
    }.get((overall_grade or "").upper(), "#00e5cc")

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                border-bottom: 3px solid {grade_color};
                padding-bottom: 15px;
                margin-bottom: 20px;
            }}
            .title {{
                font-size: 24px;
                font-weight: bold;
                color: #1f2937;
                margin: 0;
            }}
            .subtitle {{
                font-size: 14px;
                color: #6b7280;
                margin-top: 5px;
            }}
            .score-badge {{
                display: inline-block;
                background-color: {grade_color};
                color: white;
                padding: 10px 15px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                margin: 15px 0;
            }}
            .section {{
                margin: 25px 0;
                padding: 15px;
                background-color: #f9fafb;
                border-left: 4px solid {grade_color};
                border-radius: 4px;
            }}
            .section-title {{
                font-size: 16px;
                font-weight: bold;
                color: #1f2937;
                margin-top: 0;
                margin-bottom: 10px;
            }}
            .score-details {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin: 15px 0;
            }}
            .score-item {{
                background: white;
                padding: 12px;
                border-radius: 4px;
                border: 1px solid #e5e7eb;
            }}
            .score-label {{
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                color: #6b7280;
                margin-bottom: 5px;
            }}
            .score-value {{
                font-size: 18px;
                font-weight: bold;
                color: {grade_color};
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 15px;
                border-top: 1px solid #e5e7eb;
                font-size: 13px;
                color: #6b7280;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 class="title">CV Evaluation Recommendations</h1>
                <p class="subtitle">For: {candidate_name}</p>
            </div>

            <p>Dear {candidate_name},</p>

            <p>
                Thank you for submitting your CV for evaluation. We're pleased to share the results of your
                comprehensive CV assessment.
            </p>

            <div class="section">
                <h2 class="section-title">📊 Your Overall Assessment</h2>
                <div class="score-details">
                    <div class="score-item">
                        <div class="score-label">Overall Score</div>
                        <div class="score-value">{overall_score:.1f}/100</div>
                    </div>
                    <div class="score-item">
                        <div class="score-label">Overall Grade</div>
                        <div class="score-value">{(overall_grade or "N/A").upper()}</div>
                    </div>
                </div>
            </div>

            {recommendations_section}

            <div class="section">
                <h2 class="section-title">📝 Assessment Summary</h2>
                <p>{summary_interpretation}</p>
            </div>

            <p>
                We believe these insights will help you strengthen your profile and demonstrate your achievements more
                effectively. If you have any questions about this assessment, please feel free to reach out.
            </p>

            <p>Best regards,<br><strong>TALASH Evaluation Team</strong></p>

            <div class="footer">
                <p>
                    This is an automated email from the TALASH CV Evaluation System.
                    Please do not reply directly to this email.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    return html_body
