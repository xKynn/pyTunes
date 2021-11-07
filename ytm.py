from ytmusicapi import YTMusic
import os

ytmusic = YTMusic()
search_arg = ""


async def start_yt_music(search_term: str):
    # playlistId = ytmusic.create_playlist("test", "test description")
    search_results = ytmusic.search(search_term, limit=5)
    for item in search_results:
        if item['resultType'] == "song" or item['resultType'] == "video":
            video_id = item['videoId']
            break
    url = ytmusic.get_song(video_id)["microformat"]["microformatDataRenderer"]["urlCanonical"];
    os.system(f"start {url}")
