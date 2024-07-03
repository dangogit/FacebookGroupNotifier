import logging
from tkinter import *
from tkinter import messagebox, ttk

import requests

from src.monitor import FacebookMonitor

# Configuration for logging
logging.basicConfig(filename='facebook_monitor.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')


class FacebookMonitorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Facebook Group Monitor")
        self.monitor = None

        # Read access token from file
        self.access_token = self.read_access_token()
        self.create_widgets()

    def create_widgets(self):
        style = ttk.Style()
        style.configure("TLabel", font=("Arial", 10))
        style.configure("TButton", font=("Arial", 10))
        style.configure("TEntry", font=("Arial", 10))

        frame = ttk.Frame(self.root, padding="10 10 10 10")
        frame.grid(row=0, column=0, sticky=(N, W, E, S))

        for i in range(12):
            frame.rowconfigure(i, weight=1)
            frame.columnconfigure(i, weight=1)

        ttk.Label(frame, text="Group IDs (comma separated)").grid(row=1, column=0, sticky=W, pady=5)
        self.group_ids_entry = ttk.Entry(frame, width=50)
        self.group_ids_entry.grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Minimum Price").grid(row=2, column=0, sticky=W, pady=5)
        self.min_price_entry = ttk.Entry(frame)
        self.min_price_entry.grid(row=2, column=1, pady=5)

        ttk.Label(frame, text="Maximum Price").grid(row=3, column=0, sticky=W, pady=5)
        self.max_price_entry = ttk.Entry(frame)
        self.max_price_entry.grid(row=3, column=1, pady=5)

        ttk.Label(frame, text="Keywords (comma separated)").grid(row=4, column=0, sticky=W, pady=5)
        self.keywords_entry = ttk.Entry(frame, width=50)
        self.keywords_entry.grid(row=4, column=1, pady=5)

        ttk.Label(frame, text="Email Sender").grid(row=5, column=0, sticky=W, pady=5)
        self.email_sender_entry = ttk.Entry(frame, width=50)
        self.email_sender_entry.grid(row=5, column=1, pady=5)

        ttk.Label(frame, text="Email Receiver").grid(row=6, column=0, sticky=W, pady=5)
        self.email_receiver_entry = ttk.Entry(frame, width=50)
        self.email_receiver_entry.grid(row=6, column=1, pady=5)

        ttk.Label(frame, text="SMTP Server").grid(row=7, column=0, sticky=W, pady=5)
        self.smtp_server_entry = ttk.Entry(frame, width=50)
        self.smtp_server_entry.grid(row=7, column=1, pady=5)
        self.smtp_server_entry.insert(0, 'smtp.gmail.com')

        ttk.Label(frame, text="SMTP Port").grid(row=8, column=0, sticky=W, pady=5)
        self.smtp_port_entry = ttk.Entry(frame)
        self.smtp_port_entry.grid(row=8, column=1, pady=5)
        self.smtp_port_entry.insert(0, '587')

        ttk.Label(frame, text="Email Password").grid(row=9, column=0, sticky=W, pady=5)
        self.email_password_entry = ttk.Entry(frame, width=50, show='*')
        self.email_password_entry.grid(row=9, column=1, pady=5)

        ttk.Label(frame, text="Check Interval (seconds)").grid(row=10, column=0, sticky=W, pady=5)
        self.check_interval_entry = ttk.Entry(frame)
        self.check_interval_entry.grid(row=10, column=1, pady=5)
        self.check_interval_entry.insert(0, '60')

        self.start_button = ttk.Button(frame, text="Start", command=self.start_monitor)
        self.start_button.grid(row=11, column=0, pady=10)

        self.stop_button = ttk.Button(frame, text="Stop", command=self.stop_monitor)
        self.stop_button.grid(row=11, column=1, pady=10)

    def read_access_token(self):
        try:
            with open('creds.txt', 'r') as file:
                access_token = file.read().strip()
                return access_token
        except FileNotFoundError:
            logging.error("creds.txt file not found.")
            messagebox.showerror("Error", "creds.txt file not found.")
            return ""
        except Exception as e:
            logging.error(f"Error reading creds.txt: {e}")
            messagebox.showerror("Error", f"Error reading creds.txt: {e}")
            return ""

    def check_authentication(self, access_token, group_ids):
        for group_id in group_ids:
            url = f'https://graph.facebook.com/v12.0/{group_id}/feed'
            params = {'access_token': access_token}
            response = requests.get(url, params=params)
            if response.status_code != 200:
                logging.error(f"Authentication failed for group {group_id}: {response.json()}")
                messagebox.showerror("Error", f"Authentication failed for group {group_id}: {response.json()}")
                return False
        return True

    def start_monitor(self):
        if self.monitor is not None and self.monitor.is_running:
            messagebox.showerror("Error", "Monitoring is already running.")
            return

        try:
            access_token = self.access_token
            group_ids = self.group_ids_entry.get().split(',')
            min_price = int(self.min_price_entry.get())
            max_price = int(self.max_price_entry.get())
            keywords = self.keywords_entry.get().split(',')
            email_sender = self.email_sender_entry.get()
            email_receiver = self.email_receiver_entry.get()
            smtp_server = self.smtp_server_entry.get()
            smtp_port = int(self.smtp_port_entry.get())
            email_password = self.email_password_entry.get()
            check_interval = int(self.check_interval_entry.get())

            if not self.check_authentication(access_token, group_ids):
                return

            self.monitor = FacebookMonitor(access_token, group_ids, min_price, max_price, keywords,
                                           email_sender, email_receiver, smtp_server, smtp_port, email_password, check_interval)
            self.monitor.start()
            messagebox.showinfo("Info", "Monitoring started.")
        except Exception as e:
            logging.error(f"Error starting monitor: {e}")
            messagebox.showerror("Error", str(e))

    def stop_monitor(self):
        if self.monitor is not None:
            self.monitor.stop()
            self.monitor = None
            messagebox.showinfo("Info", "Monitoring stopped.")

