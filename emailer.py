# send_newsletter.py

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from dotenv import load_dotenv

load_dotenv()

def send_newsletter():

    sender_email  = os.getenv("EMAIL_ADDRESS")
    app_password  = os.getenv("EMAIL_APP_PASSWORD")
    receivers_raw = os.getenv("EMAIL_RECEIVER")
    receiver_list = [r.strip() for r in receivers_raw.split(",")]

    # =========================================
    # READ HTML — has <div class="chart-SOL"> etc
    # =========================================
    with open("newsletter.html", "r", encoding="utf-8") as f:
        html_body = f.read()

    with open("newsletter.md", "r", encoding="utf-8") as f:
        plain_body = f.read()

    # =========================================
    # FIND ALL CHART FILES
    # Replace each placeholder div with a proper
    # <img src="cid:TICKER"> inline image tag
    # =========================================
    chart_files = {}
    charts_dir = "./charts"

    if os.path.exists(charts_dir):
        for fname in os.listdir(charts_dir):
            if fname.endswith(".png"):
                ticker = fname.replace(".png", "")
                fpath  = os.path.join(charts_dir, fname)
                cid    = f"chart_{ticker}"

                # Replace the placeholder div with a real img tag
                placeholder = f'<div class="chart-{ticker}"></div>'
                img_tag = (
                    f'<div style="margin:16px 0;">'
                    f'<img src="cid:{cid}" '
                    f'style="width:100%;max-width:680px;border-radius:6px;" '
                    f'alt="{ticker} 5-day chart"/>'
                    f'</div>'
                )
                html_body = html_body.replace(placeholder, img_tag)
                chart_files[cid] = fpath

    # =========================================
    # BUILD EMAIL
    # multipart/related wraps HTML + inline images
    # multipart/alternative wraps plain + related
    # =========================================
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Daily Market Newsletter"
    msg["From"]    = sender_email
    msg["To"]      = ", ".join(receiver_list)

    # Plain text part
    msg.attach(MIMEText(plain_body, "plain"))

    # HTML + inline images wrapped in related
    related = MIMEMultipart("related")
    related.attach(MIMEText(html_body, "html"))

    # Attach each chart image with its Content-ID
    for cid, filepath in chart_files.items():
        with open(filepath, "rb") as img_file:
            img = MIMEImage(img_file.read(), _subtype="png")
            img.add_header("Content-ID", f"<{cid}>")
            img.add_header("Content-Disposition", "inline", filename=os.path.basename(filepath))
            related.attach(img)

    msg.attach(related)

    # =========================================
    # SEND
    # =========================================
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_list, msg.as_string())

    print(f"Newsletter sent to: {', '.join(receiver_list)}")


if __name__ == "__main__":
    send_newsletter()