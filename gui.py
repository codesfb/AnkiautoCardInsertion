import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading

# Import the core logic from your existing script
from anki_automator import run_card_creation_logic, ANKI_CONNECT_URL
import requests

class AnkiAutomatorApp:
    def __init__(self, root):
        self.root = root
        root.title("Anki Card Automator")

        self.log_area = scrolledtext.ScrolledText(root, width=80, height=20, state='disabled')
        self.log_area.pack(padx=10, pady=10)

        self.run_button = tk.Button(root, text="Add New Cards", command=self.start_automation_thread)
        self.run_button.pack(pady=5)

    def log_to_gui(self, message):
        """Appends a message to the GUI log area in a thread-safe way."""
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, message + '\n')
        self.log_area.configure(state='disabled')
        self.log_area.see(tk.END) # Auto-scroll to the bottom

    def run_automation(self):
        """The target function for the thread. Runs the logic and handles UI updates."""
        self.run_button.config(state='disabled')
        self.log_area.delete('1.0', tk.END) # Clear previous logs
        
        try:
            # Pass the GUI logging function to the core logic
            run_card_creation_logic(log_callback=self.log_to_gui)
        except Exception as e:
            self.log_to_gui(f"\nAn unexpected error occurred: {e}")
        finally:
            self.run_button.config(state='normal')

    def start_automation_thread(self):
        """Starts the automation in a separate thread to keep the GUI responsive."""
        # Check for Anki connection before starting the thread
        try:
            requests.get(ANKI_CONNECT_URL, timeout=2)
        except requests.exceptions.RequestException:
            messagebox.showerror("Connection Error", "Could not connect to Anki. Please ensure Anki is running with the AnkiConnect add-on.")
            return

        thread = threading.Thread(target=self.run_automation)
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = AnkiAutomatorApp(root)
    root.mainloop()