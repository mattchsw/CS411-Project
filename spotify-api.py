from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"

    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"

    }

    data = {"grant_type": "client_credentials"}

    result = post(url, headers=headers, data=data)

    json_result = json.loads(result.content)

    token = json_result["access_token"]

    return token

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

def search_for_artist(token, artist):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={artist}&type=artist&limit=1"

    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["artists"]["items"]

    if len(json_result) == 0:
        print("No artist with this name exists")
        return None
    
    return json_result[0]

def get_songs_by_artist(token, artist_id):

    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)['tracks']
    return json_result

def search_for_album(token, album):

    url = "https://api.spotify.com/v1/search"
    query = f"?q={album}&type=album&limit=1"

    query_url = url + query

    headers = get_auth_header(token)

    result = get(query_url, headers=headers)

    json_result = json.loads(result.content)["albums"]["items"]

    if len(json_result) == 0:
        print("No album with this name exists")
        return None
    

    return json_result[0]

def search_for_song(token, song):

    url = "https://api.spotify.com/v1/search"
    query = f"?q={song}&type=track&limit=1"

    query_url = url + query

    headers = get_auth_header(token)

    result = get(query_url, headers=headers)

    json_result = json.loads(result.content)["tracks"]["items"]

    if len(json_result) == 0:
        print("No song with this name exists")
        return None
    
    return json_result[0]

def get_bpm_of_song(token, song_id):
    url = f"https://api.spotify.com/v1/audio-features/{song_id}"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)
    return json_result["tempo"]

def match_songs_by_bpm(token, song_id, bpm):
    url = "https://api.spotify.com/v1/recommendations"
    headers = get_auth_header(token)
    query = f"?seed_tracks={song_id}&target_tempo={bpm}&limit=10"
    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["tracks"]
    return json_result

def get_album_tracks(token, album_id):
    url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["items"]
    return json_result

def display(songs):
    for idx, song in enumerate(songs):
        print(f"{idx + 1}, {song['name']}")


# Example usage:
if __name__ == "__main__":

    # get token
    token = get_token()
    
    # search for artist
    artist = search_for_artist(token, "Michael Jackson")["id"]
    print("Artist ID: ", artist)

    # get songs by artist
    #songs_by_artist = get_songs_by_artist(token, artist)
    #print("Songs by artist: ", songs_by_artist)

    # search for album
    album = search_for_album(token, "Off the Wall")["id"]
    print("Album ID: ", album)

    # search for song
    song = search_for_song(token, "Rock with You")["id"]
    print("Song ID: ", song)

    # get bpm of song
    bpm = get_bpm_of_song(token, song)
    print("bpm: ", bpm)

    matching_songs = match_songs_by_bpm(token, song, bpm)
    display(matching_songs)
    



