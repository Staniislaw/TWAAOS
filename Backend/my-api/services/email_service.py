import smtplib
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import os

MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_FROM = os.getenv("MAIL_FROM")

def send_registration_email(
    to_email: str,
    user_name: str,
    event_title: str,
    event_date: str,
    event_location: str,
    qr_image_base64: str = None
):
    msg = MIMEMultipart("related")  # ← "related" permite imagini embedded cu cid
    msg["Subject"] = f"✅ Confirmare înregistrare — {event_title}"
    msg["From"] = MAIL_FROM
    msg["To"] = to_email

    # Secțiunea QR în HTML — folosește cid: în loc de base64 inline
    qr_section = ""
    if qr_image_base64:
        qr_section = """
        <div style="text-align:center; margin: 24px 0;">
            <p style="font-weight:600; color:#374151; margin-bottom:12px;">🎫 Biletul tău QR</p>
            <img src="cid:qrcode"
                 style="width:200px; height:200px; border-radius:12px; border:1px solid #e5e7eb;" />
            <p style="font-size:12px; color:#9ca3af; margin-top:8px;">
                Prezintă acest cod la intrarea evenimentului
            </p>
        </div>
        """

    html = f"""
    <html>
    <body style="font-family: Inter, sans-serif; background: #f7f9fb; padding: 40px 0;">
        <div style="max-width: 520px; margin: 0 auto; background: white;
                    border-radius: 24px; overflow: hidden;
                    box-shadow: 0 8px 40px rgba(0,26,66,0.1);">
            <div style="background: linear-gradient(135deg, #003d9b, #1e429f);
                        padding: 40px 32px; text-align: center;">
                <div style="font-size: 48px;">🎓</div>
                <h1 style="color: white; font-size: 22px; margin: 16px 0 8px;">
                    Înregistrare confirmată!
                </h1>
                <p style="color: rgba(255,255,255,0.8); font-size: 14px; margin: 0;">
                    Ești oficial înscris la eveniment
                </p>
            </div>
            <div style="padding: 32px;">
                <p style="color: #374151; font-size: 15px; margin-bottom: 24px;">
                    Salut <strong>{user_name}</strong>,
                </p>
                <p style="color: #6b7280; font-size: 14px; line-height: 1.6; margin-bottom: 24px;">
                    Înregistrarea ta la evenimentul de mai jos a fost confirmată cu succes!
                </p>
                <div style="background: #f7f9fb; border-radius: 16px;
                            padding: 20px; margin-bottom: 24px;
                            border-left: 4px solid #003d9b;">
                    <h2 style="color: #1e3a8a; font-size: 18px; margin: 0 0 12px;">
                        {event_title}
                    </h2>
                    <p style="color: #6b7280; font-size: 13px; margin: 4px 0;">📅 {event_date}</p>
                    <p style="color: #6b7280; font-size: 13px; margin: 4px 0;">📍 {event_location}</p>
                </div>
                {qr_section}
                <p style="color: #9ca3af; font-size: 12px; text-align: center;
                           border-top: 1px solid #f3f4f6; padding-top: 24px; margin-top: 24px;">
                    © USV Academic Events Platform
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    # Atașezi HTML-ul
    msg_alternative = MIMEMultipart("alternative")
    msg.attach(msg_alternative)
    msg_alternative.attach(MIMEText(html, "html"))

    # Atașezi imaginea QR cu Content-ID
    if qr_image_base64:
        qr_bytes = base64.b64decode(qr_image_base64)
        qr_image = MIMEImage(qr_bytes, _subtype="png")
        qr_image.add_header("Content-ID", "<qrcode>")          # ← referit în html ca cid:qrcode
        qr_image.add_header("Content-Disposition", "inline")
        msg.attach(qr_image)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(MAIL_FROM, to_email, msg.as_string())
        print(f"Email trimis către {to_email}")
    except Exception as e:
        print(f"Eroare email: {e}")