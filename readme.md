# 🎵 Spotify → Tidal Basic GUI

A simple desktop interface for transferring your Spotify playlists into Tidal.
This project is a **fork of the incredible [spotify\_to\_tidal](https://github.com/spotify2tidal/spotify_to_tidal) tool**, created by **axel-de-block** and contributors, with a **basic GUI wrapper** added.

⚠️ **Disclaimer:** I did not create the original sync engine. Full credit and respect goes to the original authors of `spotify_to_tidal`. This project simply adds a **basic GUI wrapper** to make the tool easier to use.

---

## ✨ Features

* 🖥 Basic, straightforward GUI (no design frills, just functional)
* 🔑 Saved credentials (Spotify + Tidal login, Client ID/Secret) via `keyring`
* 📂 Config file automatically generated/updated
* 🎶 Import all playlists or just specific ones
* ❤️ Sync your "Liked Songs" with one click
* 🔄 Periodic sync support for large collections
* ⚡ Built with the same optimizations as the original CLI tool

---

## 🚀 Installation

1. Clone this fork and install it in editable mode:

```bash
git clone https://github.com/collinschepers/spotify-tidal-gui.git
cd spotify-tidal-gui
python -m pip install -e .
```

2. Install the `keyring` dependency (required for saving credentials):

```bash
python -m pip install keyring
```

> ⚠️ **Note:** Your fork already contains the original CLI files, so there’s no need to install the original repository separately.

---

## 🔧 Setup

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and create a new app.
2. Copy your **Client ID** and **Client Secret** into the GUI or config file.
3. Enter your **Spotify username** and **Tidal login details** (these will be saved for you).
4. Launch the GUI:

```bash
python spotify_tidal_gui.py
```

---

## 🖥 Usage Options

### ✅ With the GUI

* Start the GUI with `python spotify_tidal_gui.py`.
* Log in once → your details are saved.
* Choose playlists or full sync.

### ✅ With the CLI (advanced users)

You can still use the CLI commands included in this fork:

```bash
spotify_to_tidal
spotify_to_tidal --uri 1ABCDEqsABCD6EaABCDa0a
spotify_to_tidal --sync-favorites
```

Run `spotify_to_tidal --help` for more options.

---

## 🙏 Credits & Respect

* Core sync logic: [spotify\_to\_tidal](https://github.com/spotify2tidal/spotify_to_tidal) by **axel-de-block** and contributors.

Without the original tool, this GUI wouldn’t exist. Huge thanks to the authors for making playlist migration possible.
