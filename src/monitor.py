import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time
import threading
import logging

# Configuration for logging
logging.basicConfig(filename='facebook_monitor.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')


class FacebookMonitor:
    def __init__(self, access_token, group_ids, min_price, max_price, keywords, email_sender, email_receiver, smtp_server, smtp_port, email_password, check_interval):
        self.access_token = access_token
        self.group_ids = group_ids
        self.min_price = min_price
        self.max_price = max_price
        self.keywords = keywords
        self.email_sender = email_sender
        self.email_receiver = email_receiver
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_password = email_password
        self.check_interval = check_interval
        self.last_post_time = {group_id: None for group_id in group_ids}
        self.is_running = False
        self.thread = None

    def get_group_posts(self, group_id):
        try:
            url = f'https://graph.facebook.com/v12.0/{group_id}/feed'
            params = {'access_token': self.access_token}
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error fetching posts from group {group_id}: {e}")
            return None

    def filter_posts(self, posts, group_id):
        filtered_posts = []
        for post in posts['data']:
            if 'message' in post:
                message = post['message']
                created_time = post['created_time']
                price = self.extract_price(message)
                if (price and self.min_price <= price <= self.max_price and self.keywords_present(message) and
                        (self.last_post_time[group_id] is None or created_time > self.last_post_time[group_id])):
                    filtered_posts.append(post)
                    if self.last_post_time[group_id] is None or created_time > self.last_post_time[group_id]:
                        self.last_post_time[group_id] = created_time
        return filtered_posts

    def keywords_present(self, message):
        return all(keyword.lower() in message.lower() for keyword in self.keywords)

    @staticmethod
    def extract_price(message):
        import re
        prices = re.findall(r'\$\d+', message)
        if prices:
            return int(prices[0][1:])
        return None

    def send_email(self, subject, body):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_sender
            msg['To'] = self.email_receiver
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_sender, self.email_password)
                text = msg.as_string()
                server.sendmail(self.email_sender, self.email_receiver, text)
        except smtplib.SMTPException as e:
            logging.error(f"Error sending email: {e}")

    def check_new_posts(self):
        for group_id in self.group_ids:
            posts = self.get_group_posts(group_id)
            if posts:
                filtered_posts = self.filter_posts(posts, group_id)
                if filtered_posts:
                    for post in filtered_posts:
                        subject = 'New Apartment Post Matching Your Criteria'
                        body = f"New post found in group {group_id}:\n\n{post['message']}\n\nLink: https://facebook.com/{post['id']}"
                        self.send_email(subject, body)
                        logging.info(f"Email sent for post: {post['id']} in group {group_id}")

    def run(self):
        schedule.every(self.check_interval).seconds.do(self.check_new_posts)
        while self.is_running:
            schedule.run_pending()
            time.sleep(1)

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self.run)
            self.thread.start()
            logging.info("Monitoring started.")

    def stop(self):
        if self.is_running:
            self.is_running = False
            self.thread.join()
            logging.info("Monitoring stopped.")