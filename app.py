from flask import Flask, request, url_for, session, redirect, render_template, jsonify
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import logging
from dotenv import load_dotenv
import os
from werkzeug.serving import run_simple
import execjs
import applemusicpy
import jwt
import requests
import json

app = Flask(__name__)

app.secret_key = "adijnaidbajbdajbnd"
app.config['SESSION_COOKIE_NAME'] = 'Awad Cookie'
app.config.update(SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=True)
TOKEN_INFO = 'token_info'

@app.route('/')
def login():
    #in index.html when click login it will route you to /redirect
    return render_template('index.html')

@app.route('/redirect/<action>')
def redirectPage(action):
    session.clear()
    session['action'] = action
    auth_url = create_spotify_oauth().get_authorize_url()
    # code = request.args.get('code')
    # token_info = create_spotify_oauth().get_access_token(code)
    # session[TOKEN_INFO] = token_info
    #return redirect(url_for('getPlaylists', _external=True))
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    oauth = create_spotify_oauth()
    token_info = oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    action = session.get('action')
    if action == 'convert_to_spotify':
        return redirect(url_for('ConvertToSpotify'))
    else:   
        return redirect(url_for('getPlaylists', _external=True))

@app.route('/getPlaylists') #write code for getting all playlists and displaying them
def getPlaylists():
    try: 
        # get the token info from the session
        token_info = get_token()
    except:
        # if the token info is not found, redirect the user to the login route
        print('User not logged in')
        return redirect("/")
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    current_playlists =  sp.current_user_playlists()['items']
    playlist_images = [image['url'] for playlist in current_playlists for image in playlist['images']]
    playlist_names = [playlist['name'] for playlist in current_playlists]
    playlist_ids = [playlist['id'] for playlist in current_playlists]
    #app.logger.info('image url', playlist_images)
    #app.logger.info('playlist ids', playlist_ids)
    #app.logger.info('playlists', current_playlists, sp)
    # Render the playlists in the response
    #return '<br>'.join(playlist_names)
    return render_template('spotifyPlaylists.html', playlists=playlist_names, playlist_images=playlist_images, playlist_ids = playlist_ids)

@app.route('/SongsToConvert', methods=['POST'])
def SongsToConvert():
    data = request.get_json()
    playlistName = data.get('playlistName')
        # get the token info from the session
    token_info = session.get(TOKEN_INFO)
    if not token_info:
        # if the token info is not found, redirect the user to the login route
        raise Exception("No token info in session")
            #return redirect("/")
    
    #playlist_id = request.args.get('playlist')
    sp = spotipy.Spotify(auth=token_info['access_token'])
    playlist_songs = sp.playlist_items(playlistName)['items']
    isrc_list = []
    for song in playlist_songs:
        track = song.get('track')
        if track:
            external_ids = track.get('external_ids')
            if external_ids:
                isrc_code = external_ids.get('isrc')
                if isrc_code:
                    isrc_list.append(isrc_code)
    session['playlist_songs'] = isrc_list
    app.logger.info('playlist id', playlistName)
    app.logger.info('playlist songs', playlist_songs)

    return jsonify({"status": "success", "songsToConvert": "returned", "playlistName": playlistName, "redirectURL": url_for('ConvertToApple', _external=True)})


@app.route('/ConvertToApple', methods=['POST', 'GET'])
def ConvertToApple():
    isrc_list = session.get('playlist_songs')
    app.logger.info('got playlist songs in convert function', isrc_list)
    # isrc_list = []
    # for song in playlist_songs:
    #     track = song.get('track')
    #     if track:
    #         external_ids = track.get('external_ids')
    #         if external_ids:
    #             isrc_code = external_ids.get('isrc')
    #             if isrc_code:
    #                 isrc_list.append(isrc_code)
    # app.logger.info(isrc_list)
    developer_token = AppleLogin()
    return render_template('convertToApple.html', developer_token = developer_token, isrc_list= json.dumps(isrc_list))


def AppleLogin():
    private_key = os.getenv('APPLE_MUSIC_PRIVATE_KEY')
    key_id = os.getenv('APPLE_MUSIC_KEY_ID')
    team_id = os.getenv('TEAM_ID')
    time_now = int(time.time())
    time_expired = time_now + 15777000 #token valid for 6 months

    headers = {
        'alg': 'ES256',
        'kid': key_id
    }
    payload = {
        'iss': team_id,
        'exp': time_expired,
        'iat': time_now
    }
    developer_token = jwt.encode(payload, private_key, algorithm='ES256', headers=headers)
    return developer_token


@app.route('/apple_redirect')
def apple_redirect():
    developer_token = AppleLogin()
    return render_template('applemusicplaylist.html', developer_token = developer_token)

AppleMusicAuth = ''

@app.route('/receive_apple_songs', methods=['POST'])
def receive_apple_songs():
    data = request.get_json()
    songs = data.get('AppleSongsToConvert')
    session['AppleSongsToConvert'] = songs
    # Store the token securely, use it for making API calls
    # AppleMusicAuth = token  # Set global variable to token so we can use it now
    # return jsonify({"status": "success", "token": token}), 200
    #app.logger.info('received apple songs in flask back end', AppleMusicAuth)
    # redirect_url = url_for('getApplePlaylists', _external=True)
    return jsonify({"status": "success", "songs_received": len(songs), "redirectURL": url_for('ConvertToSpotify', _external=True)})

@app.route('/ConvertToSpotify')
def ConvertToSpotify():
    if 'token_info' not in session:  # Check if user is not logged in
        return redirect(url_for('redirectPage', action='convert_to_spotify'))
    token_info = get_token()
    songs = session.get('AppleSongsToConvert')
    app.logger.info("apple songs to convert", songs)
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_id = sp.current_user()['id']  # Fetch the current user's ID
    playlist_name = "Converted Playlist"  # Name your playlist
    playlist_description = "Created via Playlist Converter App"  # Provide a description for your playlist
    try:
        new_playlist = sp.user_playlist_create(user_id, playlist_name, public=True, description=playlist_description)
        playlist_id = new_playlist['id']
        app.logger.info(f"Created playlist with ID: {playlist_id}")
    except spotipy.exceptions.SpotifyException as e:
        app.logger.error(f"Failed to create playlist: {e}")
        return render_template('error.html', message="Failed to create Spotify playlist.")
    
    track_ids=[]
    for isrc in songs:
        result = sp.search(q=f'isrc:{isrc}', type='track', limit=1)
        if result['tracks']['items']:
            track_id = result['tracks']['items'][0]['id']
            track_ids.append(track_id)
    if track_ids:
        sp.user_playlist_add_tracks(user_id, playlist_id, track_ids)
        app.logger.info(f"Added tracks to playlist {playlist_id}")

    return render_template('ConvertToSpotify.html')
    

# @app.route('/getApplePlaylists')
# def getApplePlaylists():
#     return render_template('displayApplePlaylist.html', AppleMusicAuth = AppleMusicAuth, developer_token = developer_token)

def get_token():
    token_info = session.get(TOKEN_INFO)
    if not token_info:
        # if the token info is not found, redirect the user to the login route
        return None
    
    # check if the token is expired and refresh it if necessary
    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if(is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])

    return token_info


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id= os.getenv('SPOTIFY_CLIENT_ID'),
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET'),
        redirect_uri=url_for('callback', _external=True),
        scope="user-library-read playlist-modify-public playlist-modify-private",
        show_dialog=True #allows us to show login page everytime
    )

app.run(debug=True)
