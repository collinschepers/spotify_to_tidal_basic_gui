#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Spotify → TIDAL GUI wrapper for spotify_to_tidal
------------------------------------------------
- Beautiful Tkinter UI (tabs, nice layout) with persistent settings.
- Uses `keyring` to keep secrets (client_secret, TIDAL password) out of plain text.
- Builds a temporary config.yml (including secrets) ONLY when running a sync.
- Wraps the CLI: `python -m spotify_to_tidal <subcommand> [args...]`
- Shows real-time logs, allows cancel.

Requirements:
  - Python 3.8+
  - keyring (pip install keyring)  [optional but strongly recommended]
  - spotify_to_tidal installed (editable is fine): python -m pip install -e .
  - git + browser auth for Spotify on first run

Tested on Windows, but should work cross-platform.

"""

import json
import os
import sys
import tempfile
import shutil
import subprocess
import threading
import queue
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# --------- Optional secure storage ----------
try:
    import keyring
    KEYRING_AVAILABLE = True
except Exception:
    keyring = None
    KEYRING_AVAILABLE = False

APP_NAME = "spotify_to_tidal_gui"
SERVICE_NAME = "spotify_to_tidal_gui"  # for keyring
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8888/callback"  # safer than localhost per repo changes

def app_data_dir() -> Path:
    base = os.getenv("APPDATA") or os.getenv("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / APP_NAME

SETTINGS_PATH = app_data_dir() / "settings.json"

def load_settings():
    try:
        app_data_dir().mkdir(parents=True, exist_ok=True)
        if SETTINGS_PATH.exists():
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {
        "spotify_client_id": "",
        "spotify_username": "",
        "spotify_redirect_uri": DEFAULT_REDIRECT_URI,
        "tidal_username": "",
        # secrets are in keyring
        "last_playlist_url": "",
        "default_subcommand": "sync",  # change if your CLI uses a different default
    }

def save_settings(data: dict):
    app_data_dir().mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def set_secret(name: str, value: str):
    if not KEYRING_AVAILABLE:
        return False
    try:
        keyring.set_password(SERVICE_NAME, name, value or "")
        return True
    except Exception:
        return False

def get_secret(name: str) -> str:
    if not KEYRING_AVAILABLE:
        return ""
    try:
        v = keyring.get_password(SERVICE_NAME, name)
        return v or ""
    except Exception:
        return ""

class LogConsole(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.text = tk.Text(self, wrap="word", height=16, state="disabled")
        self.scroll = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=self.scroll.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        self.scroll.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def write(self, s: str):
        self.text.configure(state="normal")
        self.text.insert("end", s)
        self.text.see("end")
        self.text.configure(state="disabled")
        self.update_idletasks()

    def clear(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Spotify → TIDAL Sync (spotify_to_tidal GUI)")
        self.geometry("880x620")
        self.minsize(820, 560)
        self.style = ttk.Style(self)
        # Use a built-in theme with nice padding
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.proc = None
        self.stop_requested = False
        self.output_queue = queue.Queue()

        self.settings = load_settings()

        self._build_ui()

        # Fill with saved settings
        self._load_ui_from_settings()

    # ---------- UI ----------
    def _build_ui(self):
        container = ttk.Frame(self, padding=12)
        container.pack(fill="both", expand=True)

        title = ttk.Label(container, text="Spotify → TIDAL Sync", font=("Segoe UI", 18, "bold"))
        subtitle = ttk.Label(container, text="Beautiful wrapper for spotify_to_tidal — save credentials, run syncs, and see logs.",
                             foreground="#555")

        title.grid(row=0, column=0, sticky="w")
        subtitle.grid(row=1, column=0, sticky="w", pady=(0, 8))

        self.nb = ttk.Notebook(container)
        self.nb.grid(row=2, column=0, sticky="nsew", pady=(4, 8))

        container.grid_rowconfigure(2, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Tabs
        self.tab_setup = ttk.Frame(self.nb, padding=10)
        self.tab_sync = ttk.Frame(self.nb, padding=10)
        self.tab_advanced = ttk.Frame(self.nb, padding=10)
        self.tab_logs = ttk.Frame(self.nb, padding=10)

        self.nb.add(self.tab_setup, text="Setup")
        self.nb.add(self.tab_sync, text="Sync")
        self.nb.add(self.tab_advanced, text="Advanced")
        self.nb.add(self.tab_logs, text="Logs")

        self._build_setup_tab()
        self._build_sync_tab()
        self._build_advanced_tab()
        self._build_logs_tab()

        # Status bar
        self.status_var = tk.StringVar(value="Ready.")
        status = ttk.Label(container, textvariable=self.status_var, anchor="w")
        status.grid(row=3, column=0, sticky="ew")

    def _build_setup_tab(self):
        f = self.tab_setup

        sec_spotify = ttk.LabelFrame(f, text="Spotify Credentials", padding=10)
        sec_tidal = ttk.LabelFrame(f, text="TIDAL Credentials", padding=10)

        # Spotify
        self.var_spotify_client_id = tk.StringVar()
        self.var_spotify_client_secret = tk.StringVar()
        self.var_spotify_username = tk.StringVar()
        self.var_spotify_redirect = tk.StringVar(value=DEFAULT_REDIRECT_URI)

        ttk.Label(sec_spotify, text="Client ID").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        ttk.Entry(sec_spotify, textvariable=self.var_spotify_client_id, width=46).grid(row=0, column=1, sticky="w", padx=4, pady=4)

        ttk.Label(sec_spotify, text="Client Secret").grid(row=1, column=0, sticky="e", padx=4, pady=4)
        e_secret = ttk.Entry(sec_spotify, textvariable=self.var_spotify_client_secret, width=46, show="•")
        e_secret.grid(row=1, column=1, sticky="w", padx=4, pady=4)

        ttk.Label(sec_spotify, text="Username").grid(row=2, column=0, sticky="e", padx=4, pady=4)
        ttk.Entry(sec_spotify, textvariable=self.var_spotify_username, width=46).grid(row=2, column=1, sticky="w", padx=4, pady=4)

        ttk.Label(sec_spotify, text="Redirect URI").grid(row=3, column=0, sticky="e", padx=4, pady=4)
        ttk.Entry(sec_spotify, textvariable=self.var_spotify_redirect, width=46).grid(row=3, column=1, sticky="w", padx=4, pady=4)
        ttk.Label(sec_spotify, text="(Use 127.0.0.1, not localhost)").grid(row=3, column=2, sticky="w")

        # TIDAL
        self.var_tidal_username = tk.StringVar()
        self.var_tidal_password = tk.StringVar()

        ttk.Label(sec_tidal, text="Email / Username").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        ttk.Entry(sec_tidal, textvariable=self.var_tidal_username, width=46).grid(row=0, column=1, sticky="w", padx=4, pady=4)

        ttk.Label(sec_tidal, text="Password").grid(row=1, column=0, sticky="e", padx=4, pady=4)
        ttk.Entry(sec_tidal, textvariable=self.var_tidal_password, width=46, show="•").grid(row=1, column=1, sticky="w", padx=4, pady=4)

        # Save / Load
        btns = ttk.Frame(f)
        ttk.Button(btns, text="Save Settings", command=self.on_save_settings).pack(side="left", padx=4)
        ttk.Button(btns, text="Load Settings", command=self.on_load_settings_clicked).pack(side="left", padx=4)
        ttk.Button(btns, text="Clear Secrets", command=self.on_clear_secrets).pack(side="left", padx=4)

        # Layout
        sec_spotify.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        sec_tidal.grid(row=0, column=1, sticky="nsew")
        btns.grid(row=1, column=0, columnspan=2, sticky="w", pady=8)

        f.grid_columnconfigure(0, weight=1)
        f.grid_columnconfigure(1, weight=1)

    def _build_sync_tab(self):
        f = self.tab_sync

        sec_action = ttk.LabelFrame(f, text="Action", padding=10)
        sec_args = ttk.LabelFrame(f, text="Arguments", padding=10)
        sec_run = ttk.LabelFrame(f, text="Run", padding=10)

        self.var_action = tk.StringVar(value="sync_playlist_url")
        self.var_playlist_url = tk.StringVar()
        self.var_subcommand_custom = tk.StringVar(value=self.settings.get("default_subcommand", "sync"))
        self.var_extra_flags = tk.StringVar()

        # Action choices
        ttk.Radiobutton(sec_action, text="Sync this Spotify playlist URL", value="sync_playlist_url",
                        variable=self.var_action).grid(row=0, column=0, sticky="w", pady=2)
        ttk.Radiobutton(sec_action, text="Sync liked/favorite tracks", value="sync_favorites",
                        variable=self.var_action).grid(row=1, column=0, sticky="w", pady=2)
        ttk.Radiobutton(sec_action, text="Sync all playlists", value="sync_all_playlists",
                        variable=self.var_action).grid(row=2, column=0, sticky="w", pady=2)
        ttk.Radiobutton(sec_action, text="Custom subcommand", value="custom",
                        variable=self.var_action).grid(row=3, column=0, sticky="w", pady=2)

        # Arguments
        ttk.Label(sec_args, text="Playlist URL").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        ttk.Entry(sec_args, textvariable=self.var_playlist_url, width=64).grid(row=0, column=1, sticky="w", padx=4, pady=4)
        ttk.Label(sec_args, text="(Used when action is 'Sync playlist URL')").grid(row=0, column=2, sticky="w", padx=4)

        ttk.Label(sec_args, text="Custom subcommand").grid(row=1, column=0, sticky="e", padx=4, pady=4)
        ttk.Entry(sec_args, textvariable=self.var_subcommand_custom, width=32).grid(row=1, column=1, sticky="w", padx=4, pady=4)
        ttk.Label(sec_args, text="e.g. sync, favorites, playlists").grid(row=1, column=2, sticky="w", padx=4)

        ttk.Label(sec_args, text="Extra flags").grid(row=2, column=0, sticky="e", padx=4, pady=4)
        ttk.Entry(sec_args, textvariable=self.var_extra_flags, width=64).grid(row=2, column=1, sticky="w", padx=4, pady=4)
        ttk.Label(sec_args, text="e.g. --dry-run --no-duplicates").grid(row=2, column=2, sticky="w", padx=4)

        # Run
        ttk.Button(sec_run, text="Run", command=self.on_run).grid(row=0, column=0, padx=4, pady=4)
        ttk.Button(sec_run, text="Cancel", command=self.on_cancel).grid(row=0, column=1, padx=4, pady=4)

        # Layout
        sec_action.grid(row=0, column=0, sticky="nsew")
        sec_args.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        sec_run.grid(row=1, column=0, columnspan=2, sticky="w", pady=8)

        f.grid_columnconfigure(0, weight=1)
        f.grid_columnconfigure(1, weight=1)

    def _build_advanced_tab(self):
        f = self.tab_advanced
        desc = ("Use this if presets don’t match your installed CLI. "
                "Pick your subcommand and flags on the Sync tab. "
                "You can also choose a working directory for the process.\n\n"
                "Note: We generate a temporary config.yml that includes your secrets, "
                "pass it to the process, then delete it.")
        ttk.Label(f, text=desc, wraplength=760, foreground="#555").grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.var_work_dir = tk.StringVar(value=str(Path.cwd()))
        ttk.Label(f, text="Working directory").grid(row=1, column=0, sticky="w")
        row1 = ttk.Frame(f)
        row1.grid(row=2, column=0, sticky="ew", pady=4)
        ttk.Entry(row1, textvariable=self.var_work_dir, width=74).pack(side="left", fill="x", expand=True)
        ttk.Button(row1, text="Browse…", command=self.on_browse_workdir).pack(side="left", padx=6)

        f.grid_columnconfigure(0, weight=1)

    def _build_logs_tab(self):
        f = self.tab_logs
        self.console = LogConsole(f)
        self.console.grid(row=0, column=0, sticky="nsew")
        f.grid_rowconfigure(0, weight=1)
        f.grid_columnconfigure(0, weight=1)

        rows = ttk.Frame(f)
        rows.grid(row=1, column=0, sticky="ew", pady=6)
        ttk.Button(rows, text="Clear Logs", command=self.console.clear).pack(side="left", padx=4)

    def _load_ui_from_settings(self):
        s = self.settings
        self.var_spotify_client_id.set(s.get("spotify_client_id", ""))
        self.var_spotify_username.set(s.get("spotify_username", ""))
        self.var_spotify_redirect.set(s.get("spotify_redirect_uri", DEFAULT_REDIRECT_URI))
        self.var_tidal_username.set(s.get("tidal_username", ""))
        self.var_playlist_url.set(s.get("last_playlist_url", ""))

        if KEYRING_AVAILABLE:
            self.var_spotify_client_secret.set(get_secret("spotify_client_secret") or "")
            self.var_tidal_password.set(get_secret("tidal_password") or "")
        else:
            # Warning banner if no keyring
            messagebox.showwarning(
                "Keyring not available",
                "Python 'keyring' is not installed or not working.\n"
                "Secrets will not be saved securely. Install with:\n\n"
                "    python -m pip install keyring\n"
            )

    # ---------- Event handlers ----------
    def on_save_settings(self):
        s = self.settings
        s["spotify_client_id"] = self.var_spotify_client_id.get().strip()
        s["spotify_username"] = self.var_spotify_username.get().strip()
        s["spotify_redirect_uri"] = self.var_spotify_redirect.get().strip() or DEFAULT_REDIRECT_URI
        s["tidal_username"] = self.var_tidal_username.get().strip()
        s["last_playlist_url"] = self.var_playlist_url.get().strip()
        save_settings(s)

        ok = True
        if self.var_spotify_client_secret.get().strip():
            ok = set_secret("spotify_client_secret", self.var_spotify_client_secret.get().strip()) and ok
        if self.var_tidal_password.get().strip():
            ok = set_secret("tidal_password", self.var_tidal_password.get().strip()) and ok

        if ok or not KEYRING_AVAILABLE:
            messagebox.showinfo("Saved", "Settings saved.")
        else:
            messagebox.showwarning("Saved (with issues)",
                                  "Settings saved, but secrets may not have been stored in keyring.")

    def on_load_settings_clicked(self):
        self.settings = load_settings()
        self._load_ui_from_settings()
        self.set_status("Settings reloaded.")

    def on_clear_secrets(self):
        if not KEYRING_AVAILABLE:
            messagebox.showinfo("No keyring", "Keyring not available — nothing to clear.")
            return
        try:
            set_secret("spotify_client_secret", "")
            set_secret("tidal_password", "")
            self.var_spotify_client_secret.set("")
            self.var_tidal_password.set("")
            messagebox.showinfo("Cleared", "Secrets cleared from keyring.")
        except Exception:
            messagebox.showwarning("Error", "Could not clear secrets.")

    def on_browse_workdir(self):
        d = filedialog.askdirectory(initialdir=self.var_work_dir.get() or str(Path.cwd()))
        if d:
            self.var_work_dir.set(d)

    def set_status(self, text: str):
        self.status_var.set(text)
        self.update_idletasks()

    def on_cancel(self):
        if self.proc and self.proc.poll() is None:
            self.stop_requested = True
            try:
                self.proc.terminate()
            except Exception:
                pass
            self.set_status("Cancellation requested…")
        else:
            self.set_status("No running process.")

    def on_run(self):
        # Validate basics
        if not self.var_spotify_client_id.get().strip():
            messagebox.showerror("Missing", "Spotify Client ID is required.")
            return
        if not (self.var_spotify_client_secret.get().strip() or get_secret("spotify_client_secret")):
            messagebox.showerror("Missing", "Spotify Client Secret is required.")
            return
        if not self.var_spotify_username.get().strip():
            messagebox.showerror("Missing", "Spotify Username is required.")
            return
        if not self.var_tidal_username.get().strip():
            messagebox.showerror("Missing", "TIDAL Username is required.")
            return
        if not (self.var_tidal_password.get().strip() or get_secret("tidal_password")):
            messagebox.showerror("Missing", "TIDAL Password is required.")
            return

        # Save current UI values so they persist
        self.on_save_settings()

        # Prepare command from selections
        action = self.var_action.get()
        playlist_url = self.var_playlist_url.get().strip()
        extra_flags = self._split_flags(self.var_extra_flags.get().strip())

        if action == "sync_playlist_url":
            if not playlist_url:
                messagebox.showerror("Missing", "Please paste a Spotify playlist URL.")
                return
            subcommand = "sync"  # default common subcommand
            cmd_args = [subcommand, playlist_url]

        elif action == "sync_favorites":
            # Not all versions use the same subcommand; allow custom override via the custom field if needed.
            # Try common possibilities here:
            subcommand = "favorites"  # try 'favorites' first; change to 'sync-favorites' if your CLI needs it
            cmd_args = [subcommand]

        elif action == "sync_all_playlists":
            # Again, this varies; often it's 'playlists' or 'sync-playlists'.
            subcommand = "playlists"
            cmd_args = [subcommand]

        else:  # custom
            subcommand = self.var_subcommand_custom.get().strip() or "sync"
            cmd_args = [subcommand]
            if playlist_url:
                # If user provided a URL, pass it as next arg
                cmd_args.append(playlist_url)

        # Append extra flags
        cmd_args.extend(extra_flags)

        # Run in background thread (non-blocking UI)
        self.console.clear()
        self.set_status("Running…")
        self.stop_requested = False
        t = threading.Thread(target=self._run_worker, args=(cmd_args,), daemon=True)
        t.start()
        self.after(100, self._drain_output_queue)

    @staticmethod
    def _split_flags(s: str):
        # naive split respecting simple quotes
        import shlex
        if not s:
            return []
        try:
            return shlex.split(s)
        except Exception:
            return s.split()

    # ---------- Process runner ----------
    def _build_temp_config(self) -> Path:
        tmpdir = Path(tempfile.mkdtemp(prefix="s2t_gui_"))
        cfg = tmpdir / "config.yml"

        # Pull secrets from fields or keyring
        client_secret = self.var_spotify_client_secret.get().strip() or get_secret("spotify_client_secret")
        tidal_password = self.var_tidal_password.get().strip() or get_secret("tidal_password")

        content = [
            "spotify:",
            f"  client_id: {self.var_spotify_client_id.get().strip()}",
            f"  client_secret: {client_secret}",
            f"  username: {self.var_spotify_username.get().strip()}",
            f"  redirect_uri: {self.var_spotify_redirect.get().strip() or DEFAULT_REDIRECT_URI}",
            "",
            "tidal:",
            f"  username: {self.var_tidal_username.get().strip()}",
            f"  password: {tidal_password}",
            "",
        ]
        cfg.write_text("\n".join(content), encoding="utf-8")
        return tmpdir

    def _run_worker(self, cmd_args):
        work_dir = Path(self.var_work_dir.get().strip() or Path.cwd())
        temp_root = None
        try:
            temp_root = self._build_temp_config()
            # Run with temp config.yml as CWD so the tool finds it
            run_cwd = temp_root

            # Compose full command
            full_cmd = [sys.executable, "-m", "spotify_to_tidal"] + cmd_args

            self.output_queue.put(f"> Running: {' '.join(full_cmd)}\n")
            self.output_queue.put(f"> Using config: {run_cwd / 'config.yml'}\n\n")

            env = os.environ.copy()
            # In case your spotify_to_tidal can take env var to config, add it here.
            # env["SPOTIFY_TO_TIDAL_CONFIG"] = str(run_cwd / "config.yml")

            self.proc = subprocess.Popen(
                full_cmd,
                cwd=run_cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
            )

            for line in self.proc.stdout:
                if self.stop_requested:
                    break
                self.output_queue.put(line)

            rc = self.proc.wait()
            if self.stop_requested:
                self.output_queue.put("\nProcess terminated by user.\n")
            elif rc == 0:
                self.output_queue.put("\n✓ Done. Exit code 0.\n")
            else:
                self.output_queue.put(f"\n✗ Finished with exit code {rc}.\n")
        except FileNotFoundError as e:
            self.output_queue.put(f"\n✗ Error: {e}\n"
                                  "Make sure 'spotify_to_tidal' is installed and Python can run it.\n")
        except Exception as e:
            self.output_queue.put(f"\n✗ Unexpected error: {e}\n")
        finally:
            # Clean up temp dir (remove secrets from disk)
            if temp_root and temp_root.exists():
                try:
                    shutil.rmtree(temp_root, ignore_errors=True)
                    self.output_queue.put("Temporary config removed.\n")
                except Exception:
                    self.output_queue.put("Warning: could not remove temporary config.\n")
            self.proc = None
            self.after(0, lambda: self.set_status("Ready."))

    def _drain_output_queue(self):
        try:
            while True:
                line = self.output_queue.get_nowait()
                self.console.write(line)
        except queue.Empty:
            pass
        # Keep polling while a process is (or might be) running
        if self.proc is not None and self.proc.poll() is None:
            self.after(100, self._drain_output_queue)
        else:
            # one last sweep after process exits
            if not self.output_queue.empty():
                self.after(100, self._drain_output_queue)

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
