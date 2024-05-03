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

app = Flask(__name__)

app.secret_key = "adijnaidbajbdajbnd"
app.config['SESSION_COOKIE_NAME'] = 'Awad Cookie'
TOKEN_INFO = 'token_info'

@app.route('/')
def login():
    #in index.html when click login it will route you to /redirect
    return render_template('index.html')

@app.route('/redirect')
def redirectPage():
    auth_url = create_spotify_oauth().get_authorize_url()
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
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

songstoconvert=[]

@app.route('/SongsToConvert')
def SongsToConvert():
    try: 
        # get the token info from the session
        token_info = get_token()
    except:
        # if the token info is not found, redirect the user to the login route
        print('User not logged in')
        return redirect("/")
    
    playlist_id = request.args.get('playlist')
    sp = spotipy.Spotify(auth=token_info['access_token'])
    playlist_songs = sp.playlist_items(playlist_id)['items']

    app.logger.info('playlist id', playlist_id)
    app.logger.info('playlist songs', playlist_songs)


    return "songstoconvert called successfully"

developer_token=[]
@app.route('/apple_redirect')
def apple_redirect():
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
    return render_template('applemusicplaylist.html', developer_token = developer_token)
    #return redirect(url_for('getApplePlaylists', _external=True))

@app.route('/getApplePlaylists')
def getApplePlaylists():
    return developer_token

def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        # if the token info is not found, redirect the user to the login route
        redirect(url_for('login', _external=False))
    
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
        redirect_uri=url_for('redirectPage', _external=True),
        scope="user-library-read playlist-modify-public playlist-modify-private"
    )

app.run(debug=True)
