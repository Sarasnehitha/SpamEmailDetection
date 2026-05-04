import imaplib
import email
from email.header import decode_header
import streamlit as st
from bs4 import BeautifulSoup
import re

def connect_to_email(server, user, password):
    try:
        mail = imaplib.IMAP4_SSL(server)
        mail.login(user, password)
        return mail
    except Exception as e:
        st.error(f"Failed to connect: {e}")
        return None

def get_emails(mail, limit=10):
    emails_data = []
    try:
        mail.select("INBOX")
        _, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()
        
        # Get the latest emails
        for i in range(len(email_ids), len(email_ids) - limit, -1):
            if i <= 0:
                break
            
            _, msg_data = mail.fetch(email_ids[i-1], "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    
                    sender, encoding = decode_header(msg.get("From"))[0]
                    if isinstance(sender, bytes):
                        sender = sender.decode(encoding if encoding else "utf-8")
                    
                    date = msg.get("Date")
                    
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))
                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                body = part.get_payload(decode=True).decode()
                                break
                            elif content_type == "text/html" and "attachment" not in content_disposition:
                                html_body = part.get_payload(decode=True).decode()
                                soup = BeautifulSoup(html_body, "html.parser")
                                body = soup.get_text()
                                break
                    else:
                        body = msg.get_payload(decode=True).decode()
                    
                    emails_data.append({
                        "id": email_ids[i-1].decode(),
                        "subject": subject,
                        "sender": sender,
                        "date": date,
                        "body": body
                    })
    except Exception as e:
        st.error(f"Error fetching emails: {e}")
    
    return emails_data

def clean_text_robust(text):
    if not text:
        return ""
    # Remove HTML tags if any left
    text = BeautifulSoup(text, "html.parser").get_text()
    # Remove special characters and digits
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    # Convert to lowercase
    text = text.lower()
    return text

def extract_urls(text):
    if not text:
        return []
    # Standard URL regex
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)

def check_phishing_risk(text):
    urls = extract_urls(text)
    if not urls:
        return 0
    
    risk_score = 0
    suspicious_keywords = ['login', 'verify', 'account', 'update', 'secure', 'banking', 'prize', 'gift']
    shortener_domains = ['bit.ly', 'goo.gl', 't.co', 'tinyurl.com', 'is.gd', 'buff.ly', 'ow.ly']
    
    for url in urls:
        # Check for URL shorteners
        if any(domain in url.lower() for domain in shortener_domains):
            risk_score += 40
        
        # Check for suspicious keywords in URL
        if any(keyword in url.lower() for keyword in suspicious_keywords):
            risk_score += 20
            
    # Cap at 100
    return min(risk_score, 100)
