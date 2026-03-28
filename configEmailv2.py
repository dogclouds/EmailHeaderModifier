import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import re
from pathlib import Path


STRIP_HEADERS = {
    "delivered-to",
    "x-received",
    "arc-seal",
    "arc-message-signature",
    "arc-authentication-results",
    "authentication-results",
    "return-path",
    "received-spf",
    "dkim-signature",
}


def process_email(content):
    content = re.sub(
        r'^(From:.*?<[^@<>]+)@[^<>]+(>)',
        r'\1@[P_RPATH]\2',
        content,
        flags=re.MULTILINE
    )
    if re.search(r'^Sender:', content, flags=re.MULTILINE | re.IGNORECASE):
        content = re.sub(
            r'^(Sender:.*?)@[^\s>]+',
            r'\1@[RDNS]',
            content,
            flags=re.MULTILINE | re.IGNORECASE
        )
    else:
        content = re.sub(
            r'^(From:.*)$',
            r'\1\nSender: support@[RDNS]',
            content,
            flags=re.MULTILINE
        )
    content = re.sub(
        r'^(Message-ID:\s*<?[^@\s<>]+)@',
        r'\1[EID]@',
        content,
        flags=re.MULTILINE | re.IGNORECASE
    )
    return content


def process_email_plus(content):
    # Run the standard processing first
    content = process_email(content)

    # Strip unwanted headers (handles multi-line folded headers too)
    lines = content.splitlines()
    filtered = []
    skip = False
    for line in lines:
        # A folded continuation line starts with whitespace
        if skip and line and line[0] in (" ", "\t"):
            continue
        skip = False
        # Check if this line is a header we want to remove
        match = re.match(r'^([A-Za-z0-9_-]+)\s*:', line)
        if match and match.group(1).lower() in STRIP_HEADERS:
            skip = True
            continue
        filtered.append(line)
    content = "\n".join(filtered)

    # Add CC: [*to] if CC is absent
    if not re.search(r'^CC\s*:', content, flags=re.MULTILINE | re.IGNORECASE):
        content = re.sub(
            r'^(To:.*)$',
            r'\1\nCC: [*to]',
            content,
            flags=re.MULTILINE
        )

    return content


class EmailProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Email Processor")
        self.root.state("zoomed")
        self.root.configure(bg="#1e1e2e")

        self.input_path = None

        title = tk.Label(
            root, text="📧 Email Header Processor",
            font=("Segoe UI", 16, "bold"),
            bg="#1e1e2e", fg="#cdd6f4"
        )
        title.pack(pady=(16, 4))

        subtitle = tk.Label(
            root, text="Paste your email content below and click Process",
            font=("Segoe UI", 9),
            bg="#1e1e2e", fg="#6c7086"
        )
        subtitle.pack(pady=(0, 12))

        btn_frame = tk.Frame(root, bg="#1e1e2e")
        btn_frame.pack(pady=(0, 10))

        self._btn(btn_frame, "⚡ Process", self.process, "#a6e3a1").pack(side="left", padx=6)
        self._btn(btn_frame, "⚡ Process+", self.process_plus, "#89b4fa").pack(side="left", padx=6)
        self._btn(btn_frame, "💾 Save Output", self.save_file, "#f38ba8").pack(side="left", padx=6)
        self._btn(btn_frame, "🗑 Clear", self.clear_all, "#6c7086").pack(side="left", padx=6)

        self.pane = tk.PanedWindow(root, orient="horizontal", bg="#313244", sashwidth=5)
        self.pane.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self.input_box = self._editor(self.pane, "Input — Paste email here")
        self.output_box = self._editor(self.pane, "Output")
        self.pane.add(self.input_box["frame"], minsize=300)
        self.pane.add(self.output_box["frame"], minsize=300)

        # Force 50/50 after window is fully drawn
        root.after(100, lambda: self.pane.sash_place(0, root.winfo_width() // 2, 0))

        self.status = tk.Label(
            root, text="Ready — paste your email in the Input box and click Process",
            font=("Segoe UI", 9),
            bg="#313244", fg="#a6e3a1",
            anchor="w", padx=10
        )
        self.status.pack(fill="x", side="bottom")

    def _btn(self, parent, text, cmd, color):
        return tk.Button(
            parent, text=text, command=cmd,
            bg=color, fg="#1e1e2e",
            font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2",
            padx=12, pady=6,
            activebackground=color, activeforeground="#1e1e2e"
        )

    def _editor(self, parent, label_text):
        frame = tk.Frame(parent, bg="#1e1e2e")
        lbl = tk.Label(
            frame, text=label_text,
            font=("Segoe UI", 10, "bold"),
            bg="#1e1e2e", fg="#cdd6f4"
        )
        lbl.pack(anchor="w", padx=4, pady=(4, 2))
        box = scrolledtext.ScrolledText(
            frame,
            font=("Consolas", 10),
            bg="#181825", fg="#cdd6f4",
            insertbackground="#cdd6f4",
            relief="flat", wrap="none",
            selectbackground="#45475a"
        )
        box.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        return {"frame": frame, "box": box}

    def set_status(self, msg, color="#a6e3a1"):
        self.status.config(text=msg, fg=color)

    def process(self):
        raw = self.input_box["box"].get("1.0", "end-1c").strip()
        if not raw:
            messagebox.showwarning("No input", "Please paste email content in the Input box first.")
            return
        result = process_email(raw)
        self.output_box["box"].delete("1.0", "end")
        self.output_box["box"].insert("1.0", result)
        self.set_status("⚡ Processing complete")

    def process_plus(self):
        raw = self.input_box["box"].get("1.0", "end-1c").strip()
        if not raw:
            messagebox.showwarning("No input", "Please paste email content in the Input box first.")
            return
        result = process_email_plus(raw)
        self.output_box["box"].delete("1.0", "end")
        self.output_box["box"].insert("1.0", result)
        self.set_status("⚡ Process+ complete — headers stripped, CC injected")

    def save_file(self):
        output = self.output_box["box"].get("1.0", "end-1c").strip()
        if not output:
            messagebox.showwarning("Nothing to save", "Process an email first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile="updatedEmail.txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            Path(path).write_text(output, encoding="utf-8")
            self.set_status(f"💾 Saved to {Path(path).name}")

    def clear_all(self):
        self.input_box["box"].delete("1.0", "end")
        self.output_box["box"].delete("1.0", "end")
        self.set_status("🗑 Cleared")


if __name__ == "__main__":
    root = tk.Tk()
    app = EmailProcessorApp(root)
    root.mainloop()
