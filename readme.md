🎵 Spotify → Tidal Basic GUI

A simple desktop interface for transferring your Spotify playlists into Tidal.
This project is built on top of the incredible spotify_to_tidal command-line tool, created by axel-de-block and contributors.

⚠️ Disclaimer: I did not create the original sync engine. Full credit and respect goes to the original authors of spotify_to_tidal. This project simply adds a basic GUI wrapper to make the tool easier to use.

✨ Features

🖥 Basic, straightforward GUI (no design frills, just functional)

🔑 Saved credentials (Spotify + Tidal login, Client ID/Secret) via keyring

📂 Config file automatically generated/updated

🎶 Import all playlists or just specific ones

❤️ Sync your "Liked Songs" with one click

🔄 Periodic sync support for large collections

⚡ Built with the same optimizations as the original CLI tool

🚀 Installation

⚠️ Step 1 — Install the original spotify_to_tidal tool (required):

git clone https://github.com/spotify2tidal/spotify_to_tidal.git
cd spotify_to_tidal
python -m pip install -e .


⚠️ Step 2 — Install the keyring dependency (required for saving credentials):

python -m pip install keyring


Step 3 — Install this GUI wrapper:

git clone https://github.com/collinschepers/spotify-tidal-gui.git
cd spotify-tidal-gui
python -m pip install -e .


This will link both the original CLI tool and the GUI wrapper.

🔧 Setup

Go to the Spotify Developer Dashboard and create a new app.

Copy your Client ID and Client Secret into the GUI or config file.

Enter your Spotify username and Tidal login details (these will be saved for you).

Launch the GUI:

python spotify_tidal_gui.py

🖥 Usage Options
✅ With the GUI

Start the GUI with python spotify_tidal_gui.py.

Log in once → your details are saved.

Choose playlists or full sync.

✅ With the original CLI (advanced users)

You can still use the original spotify_to_tidal commands directly, for example:

spotify_to_tidal
spotify_to_tidal --uri 1ABCDEqsABCD6EaABCDa0a
spotify_to_tidal --sync-favorites


Run spotify_to_tidal --help for more options.

🙏 Credits & Respect

Core sync logic: spotify_to_tidal by axel-de-block and contributors.

GUI wrapper & usability layer: Collin Schepers (Fuzz Face)

Without the original tool, this GUI wouldn’t exist. Huge thanks to the authors for making playlist migration possible.
