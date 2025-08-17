# Spotify → Tidal GUI

A modern, user-friendly **Graphical User Interface** built on top of the excellent [`spotify_to_tidal`](https://github.com/spotify2tidal/spotify_to_tidal) command line tool.
This project makes it simple to sync your Spotify playlists into your Tidal account without needing to touch the command line.

⚠️ **Important:** I did **not** create the original `spotify_to_tidal` tool. Full credit and respect go to [axel-de-block](https://github.com/axel-de-block) and all contributors for building and maintaining it. My work is purely an **interface layer (GUI)** to make the tool more accessible to everyday users.

---

## ✨ Features

* 🎨 Clean and intuitive interface (Tkinter-based).
* 🔑 Save your Spotify & Tidal credentials securely, so you don’t have to re-enter them every session.
* 🎶 Import a single playlist by pasting its Spotify link.
* 💿 Sync your entire Spotify library into Tidal with one click.
* ❤️ Quick-sync of your **Liked Songs**.
* ⚙️ Built on top of `spotify_to_tidal` – so all command line features are still available, just more accessible.

---

## 🚀 Installation

Clone this repository and install requirements:

```bash
git clone https://github.com/YOURUSERNAME/spotify-tidal-gui.git
cd spotify-tidal-gui
pip install -r requirements.txt
```

---

## 🔧 Setup

1. Register a new Spotify app: [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Copy your **Client ID** and **Client Secret**.
3. Launch the GUI and enter your Spotify + Tidal credentials in the settings panel (they’ll be saved for next time).

---

## 🎵 Usage

Run the GUI with:

```bash
python spotify_tidal_gui.py
```

* Paste a playlist link to sync just that playlist.
* Use the "Sync All" button to bring your entire Spotify collection into Tidal.
* Use "Sync Favorites" to import your liked songs.

---

## 🙏 Acknowledgements

* Huge thanks to the [`spotify_to_tidal`](https://github.com/spotify2tidal/spotify_to_tidal) team for their incredible work.
* This GUI would not exist without their project. Please consider contributing to the original repo if you’d like to support ongoing development of the core tool.

---

Do you want me to also design a **screenshot/demo mockup section** for your README so it looks even more professional?
