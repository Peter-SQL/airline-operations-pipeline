import os
import smtplib
from email.message import EmailMessage


smtp_host = "smtp.web.de"
smtp_port = 587

smtp_user = os.getenv("AIRFLOW_SMTP_USER")
smtp_password = os.getenv("AIRFLOW_SMTP_PASSWORD")
smtp_from = os.getenv("AIRFLOW_SMTP_FROM")

if not smtp_user:
    raise ValueError("AIRFLOW_SMTP_USER is not set.")

if not smtp_password:
    raise ValueError("AIRFLOW_SMTP_PASSWORD is not set.")

if not smtp_from:
    raise ValueError("AIRFLOW_SMTP_FROM is not set.")


message = EmailMessage()

message["Subject"] = "Airflow SMTP Test"
message["From"] = smtp_from
message["To"] = smtp_user

message.set_content(
    "SMTP-Test erfolgreich.\n\n"
    "Diese E-Mail wurde aus dem "
    "Airline-Airflow-Docker-Container gesendet."
)


print(f"Connecting to {smtp_host}:{smtp_port} ...")

with smtplib.SMTP(smtp_host, smtp_port) as server:
    server.ehlo()
    server.starttls()
    server.ehlo()

    print("Logging in ...")

    server.login(
        smtp_user,
        smtp_password,
    )

    print("Sending test email ...")

    server.send_message(message)


print("Test email sent successfully.")