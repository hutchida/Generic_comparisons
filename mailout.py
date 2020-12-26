    
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

#receiver_email_list should be in semi colon space separate string

def send(subject, html, receiver_email_list, sender_email):    
    recipients = receiver_email_list.split('; ')
    #recipients = []
    #for receiver_email in receiver_email_list: recipients.append(receiver_email)

    #format email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email    
    msg["To"] = ", ".join(recipients)
    
    HTMLPart = MIMEText(html, "html")
    msg.attach(HTMLPart)

    #send email
    s = smtplib.SMTP("LNGWOKEXCP002.legal.regn.net")
    s.sendmail(sender_email, recipients, msg.as_string())