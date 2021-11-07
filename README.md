# pyTunes
HackNC 2021 Project

<img src="https://github.com/xKynn/pyTunes/raw/main/meta/pyTunes-showcase.gif" width=30%>

## Setting Up
Once the repo is cloned, install the requirements through `pip install -r ./requirements.txt`
Once that is done, edit `configure.py` with your AssemblyAI authorization key.

## First Launch
When you first launch pyTunes, you'll need to login through Spotify in a pop-up. Once that's done, pyTunes is ready to use!

## Usage
You need to use the keyword `play` when speaking. 

Examples: `play pop music`, `play pop`, `play edm`.

## YTMusic
YouTube Music is used as a fallback for if you don't have a Spotify premium account, which Spotify needs you to for these API calls.

Alternatively, `yt_main.py` can be run for those who only want to use YouTube Music to search for songs.

To run `yt_main.py` the AssemblyAI authorization key needs to be added to the top of the file. 

No YT music login required.

`yt_main.py` demo
https://user-images.githubusercontent.com/65694382/140658583-35f7785b-14d3-4ad5-8ff9-6325e767a365.mp4

