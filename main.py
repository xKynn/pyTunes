import websockets
import asyncio
import base64
import json
import pyaudio
import os
import spotipy

from multiprocessing import Process, Queue, Pipe
from configure import auth_key, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, SPOTIFY_USERNAME
from ui import uifunc
from ytm import start_yt_music
from spotipy.oauth2 import SpotifyOAuth


os.environ["SPOTIPY_CLIENT_ID"] = SPOTIPY_CLIENT_ID
os.environ["SPOTIPY_CLIENT_SECRET"] = SPOTIPY_CLIENT_SECRET
os.environ["SPOTIPY_REDIRECT_URI"] = SPOTIPY_REDIRECT_URI

is_fully_processed = False
SONGS_QUANT = 20

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="user-library-read,user-modify-playback-state,user-read-playback-state"))
user = sp.user(SPOTIFY_USERNAME)

# Lazy caching of tracks, we cache tracks only when we need to fulfill SONG_QUANT
# and there wasn't enough in the first 50

lazy_track_cache = {
    'tracks': [],
    'last_offset': 0
}

# Temp local queue, we wipe this after we queue tracks

local_queue = []

FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
p = pyaudio.PyAudio()

# starts recording
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=FRAMES_PER_BUFFER
)


# the AssemblyAI endpoint we're going to hit
URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"

# Load 50 tracks from starting offset, dump into cache

async def load_user_tracks():

    tracks = sp.current_user_saved_tracks(limit=50, offset=lazy_track_cache['last_offset'])
    lazy_track_cache['tracks'].extend(tracks['items'])
    lazy_track_cache['last_offset'] = lazy_track_cache['last_offset'] + 50

    # If there were less tracks than our request, we are at the end of the users list
    if len(tracks) < 50:
        is_fully_processed = True

# Filter songs by artists' genre tags

async def filter_genres(genre: str, tracks: list):
    # double worded tags like "nu metal"
    # TODO: Make more accurate, can match "nu"
    if not tracks:
        return
    if len(genre.split(" ")) > 1:
        genre = genre.split(" ")
    elif len(genre.split("-")) > 1:
        genre = genre.split("-")


    # Try to match genres

    for track in tracks:

        if len(local_queue) >= SONGS_QUANT:
            break
        tg = sp.artist(track['track']['artists'][0]['id'])['genres']
        if type(genre) != str:
            for gen in genre:
                if gen.lower() in tg:
                    local_queue.append(track['track']['uri'])
                    break
        elif genre.lower() in tg:

            local_queue.append(track['track']['uri'])

    print(local_queue)

async def recommend(genre: str):
    # Try to filter genres with cached tracks
    # If QUANT isn't satisfied we go agane

    if len(lazy_track_cache['tracks']) != 0:
        await filter_genres(genre, lazy_track_cache['tracks'])
    else:
        await load_user_tracks()
        await filter_genres(genre, lazy_track_cache['tracks'])

    offset = 50
    while(len(local_queue) < SONGS_QUANT and not is_fully_processed):
        await load_user_tracks()
        await asyncio.sleep(1)
        if (lazy_track_cache['tracks'][offset:]):
            await filter_genres(genre, lazy_track_cache['tracks'][offset:])
            await asyncio.sleep(1)
        offset += 50


async def queue_local_tracks():
    # List Devices
    devs = sp.devices()

    main_device = None
    for dev in devs['devices']:
        if dev['is_active']:
            main_device = dev
    if not main_device and devs['devices']:
        # If there was no active device pick the first one
        main_device = devs['devices'][0]

    print(main_device)

    # If our selected device isnt active, start playing the first song so we have access to a queue
    if not main_device['is_active']:
        sp.start_playback(device_id=main_device['id'], uris=[local_queue[0],])
        await asyncio.sleep(3)
        for track in local_queue[1:]:
            sp.add_to_queue(track)
            await asyncio.sleep(0.3)
    else:
        for track in local_queue:
            sp.add_to_queue(track)
            await asyncio.sleep(0.3)

    # Clear our local queue
    local_queue.clear()
    try:
        # Play regardless of if we are playing or not, if we fail sweep it under the rug
        sp.start_playback()
    except:
        pass


async def send_receive():
    print('Waiting for Alt + X')
    # keyboard.wait('alt+x')
    async with websockets.connect(
            URL,
            extra_headers=(("Authorization", auth_key),),
            ping_interval=5,
            ping_timeout=20
    ) as _ws:
        await asyncio.sleep(0.1)
        print("Receiving SessionBegins ...")
        session_begins = await _ws.recv()
        print(session_begins)
        print("Sending messages ...")
        while True:
            try:
                if pc.poll():
                    if (pc.recv() == "listen"):
                        break
                await asyncio.sleep(0.02)
            except:
                pass
        pc.send("Listening...")
        async def send():
            while True:
                try:
                    data = stream.read(FRAMES_PER_BUFFER)
                    data = base64.b64encode(data).decode("utf-8")
                    json_data = json.dumps({"audio_data": str(data)})
                    await _ws.send(json_data)
                except websockets.exceptions.ConnectionClosedError as e:
                    print(e)
                    assert e.code == 4008
                    break
                except Exception as e:
                    assert False, "Not a websocket 4008 error"
                await asyncio.sleep(0.01)

            return True

        async def receive():
            while True:
                try:
                    result_str = await _ws.recv()
                    pc.send(json.loads(result_str)['text'])
                    txt = json.loads(result_str)['text'].lower()
                    if "play" in txt:

                        if len(txt.split(" ")) <= 1:
                            continue
                        else:
                            try:
                                gen = " ".join(txt.split("play")[1:]).strip()
                                pc.send(f"Looking for the best {gen} tracks...")
                                await recommend(" ".join(txt.split("play")[1:]).strip())
                                pc.send(f"Queueing them up...")
                                await queue_local_tracks()
                                pc.send("")
                                break
                            except:
                                pc.send(f"Falling back to YTMusic...")
                                await start_yt_music(" ".join(txt.split("play")[1:]).strip())
                                pc.send("")
                    if "cancel" in txt or "exit" in txt:
                        break
                except websockets.exceptions.ConnectionClosedError as e:
                    print(e)
                    assert e.code == 4008
                    break
                except Exception as e:
                    assert False, "Not a websocket 4008 error"

        send_result, receive_result = await asyncio.gather(send(), receive())


if __name__ == "__main__":
    pc, cc = Pipe()
    p = Process(target=uifunc, args=(cc, ))
    p.start()
    while 1:
        try:
            asyncio.run(send_receive())
        except:
            pass
