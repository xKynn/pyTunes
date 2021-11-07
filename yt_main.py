auth_key = "<auth key>"

import pyaudio
from ytmusicapi import YTMusic
import os


ytmusic = YTMusic()
search_arg = ""

async def start_yt_music(search_term: str):     
        #playlistId = ytmusic.create_playlist("test", "test description")
        search_results = ytmusic.search(search_term, limit = 5)
        for item in search_results:
            if item['resultType'] == "song" or item['resultType'] == "video":
                video_id = item['videoId']
                break
        url = ytmusic.get_song(video_id)["microformat"]["microformatDataRenderer"]["urlCanonical"];
        os.system(f"start {url}")
 
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
import websockets
import asyncio
import base64
import json
 
# the AssemblyAI endpoint we're going to hit
URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"
 
async def send_receive():
   print(f'Connecting websocket to url ${URL}\n')
   async with websockets.connect(
       URL,
       extra_headers=(("Authorization", auth_key),),
       ping_interval=5,
       ping_timeout=20
   ) as _ws:
       await asyncio.sleep(0.1)

       session_begins = await _ws.recv()
       
       print("(Say 'play (song)' ex: 'play Fur Elise by Beethoven')")
       print("Listening ...")
       async def send():
           while True:
               try:
                   data = stream.read(FRAMES_PER_BUFFER)
                   data = base64.b64encode(data).decode("utf-8")
                   json_data = json.dumps({"audio_data":str(data)})
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
           global search_arg
           while True:
               try:
                    result_str = await _ws.recv()
                    str_res = json.loads(result_str)['text'].lower()
                    print(str_res, end="\r")
                    if "play" in str_res:
                        play_split = str_res.split("play ")
                        if len(play_split) >= 2:
                            search_arg = play_split
                    if (str_res == "") and (search_arg != ""):
                        print(f"Searching YT music for: {search_arg[1]}")
                        await start_yt_music(search_arg[1][:-1]) # [:-1] removes period at the end 
                        break
               except websockets.exceptions.ConnectionClosedError as e:
                   print(e)
                   assert e.code == 4008
                   break
               except Exception as e:
                   assert False, "Not a websocket 4008 error"
      
       send_result, receive_result = await asyncio.gather(send(), receive())
asyncio.run(send_receive())