import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import requests

# Import the core logic from your existing script
from anki_automator import run_card_creation_logic, ANKI_CONNECT_URL

class AnkiAutomatorApp:
    def __init__(self, root):
        self.root = root
        root.title("Anki Card Automator")
        root.geometry("600x450")
        root.configure(bg="#F0F0F0") # Anki-like light grey background

        # Use ttk for a more modern look
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # --- Main Frame ---
        main_frame = tk.Frame(root, bg="#F0F0F0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Log Area ---
        log_frame = tk.Frame(main_frame, bd=1, relief=tk.SUNKEN)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_area = scrolledtext.ScrolledText(
            log_frame,
            width=80,
            height=20,
            state='disabled',
            wrap=tk.WORD,
            bg="white",
            font=("Helvetica", 10)
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # --- Bottom Frame for Controls ---
        bottom_frame = tk.Frame(root, bg="#F0F0F0")
        bottom_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # --- Run Button ---
        self.run_button = ttk.Button(
            bottom_frame,
            text="Add New Cards",
            command=self.start_automation_thread,
            style="Accent.TButton"
        )
        self.run_button.pack(pady=5, fill=tk.X)
        self.style.configure("Accent.TButton", font=("Helvetica", 10, "bold"), padding=6)

        # --- Status Bar ---
        self.status_var = tk.StringVar()
        status_bar = tk.Label(
            root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, bg="#DFDFDF"
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.check_anki_connection_status()

    def log_to_gui(self, message):
        """Appends a message to the GUI log area in a thread-safe way."""
        def _append():
            self.log_area.configure(state='normal')
            self.log_area.insert(tk.END, message + '\n')
            self.log_area.configure(state='disabled')
            self.log_area.see(tk.END)
        self.root.after(0, _append)

    def run_automation(self):
        """The target function for the thread. Runs the logic and handles UI updates."""
        self.root.after(0, lambda: self.run_button.config(state='disabled'))
        self.root.after(0, lambda: self.status_var.set("Processing..."))
        
        def _clear_log():
            self.log_area.configure(state='normal')
            self.log_area.delete('1.0', tk.END)
            self.log_area.configure(state='disabled')
        self.root.after(0, _clear_log)
        
        try:
            run_card_creation_logic(log_callback=self.log_to_gui)
            self.root.after(0, lambda: self.status_var.set("Done!"))
        except Exception as e:
            self.log_to_gui(f"\nAn unexpected error occurred: {e}")
            self.root.after(0, lambda: self.status_var.set("Error!"))
        finally:
            self.root.after(0, lambda: self.run_button.config(state='normal'))

    def start_automation_thread(self):
        """Starts the automation in a separate thread to keep the GUI responsive."""
        if not self.check_anki_connection_status():
            messagebox.showerror("Connection Error", "Could not connect to Anki. Please ensure Anki is running with the AnkiConnect add-on.")
            return

        thread = threading.Thread(target=self.run_automation, daemon=True)
        thread.start()

    def check_anki_connection_status(self):
        """Checks connection to Anki and updates status bar. Returns True if connected."""
        try:
            requests.get(ANKI_CONNECT_URL, timeout=1)
            self.status_var.set("Ready. Connected to Anki.")
            return True
        except requests.exceptions.RequestException:
            self.status_var.set("Disconnected. Please start Anki with AnkiConnect.")
            return False

if __name__ == "__main__":
    root = tk.Tk()
    app = AnkiAutomatorApp(root)
    root.mainloop()