
from flask import Flask, redirect, url_for, session, request, jsonify, Markup
from flask_oauthlib.client import OAuth
from flask import render_template
from time import localtime, strftime
from bson.objectid import ObjectId
from threading import Lock
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

import pprint
import os
import json
import pymongo
import dns
import sys

app = Flask(__name__)
socketio = SocketIO(app, async_mode=None)
usernum=0
thread1 = None
usernum_lock=Lock()
thread1_lock = Lock()
thread2 = None
thread2_lock = Lock()

app.debug = True #Change this to False for production
app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)


    #Set up GitHub as OAuth provider
github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'], #your web app's "username" for github's OAuth
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],#your web app's "password" for github's OAuth
    request_token_params={'scope': 'user:email'}, #request read-only access to the user's email.  For a list of possible scopes, see developer.github.com/apps/building-oauth-apps/scopes-for-oauth-apps
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize' #URL for github's OAuth login
)

#TODO: globalVar=postData Create and set a global variable for the name of you JSON file here.  The file will be storedd on Heroku, so you don't need to make it in GitHub
#TODO: Create the file on Heroku using os.system.  Ex) os.system("echo '[]'>"+myFile) puts '[]' into your file
#os.system("echo '[]'>"+pdata)

def background_thread1():
    count=0
    while True:
        socketio.sleep(5) #wait 5 seconds
        count=count+1
        socketio.emit('count_event1', count) #sends out the varible count to all of the cleints

def background_thread2():
    count=0
    while True:
        socketio.sleep(5) #wait 5 seconds
        count=count+1
        socketio.emit('count_event2', count) #sends out the varible count to all of the cleints

@socketio.on('connect')
def test_connect():
    global usernum
    with usernum_lock:
        print(usernum)
        if usernum >= 2:
            if session['user_data']['login'] == '':
                yeet='yeet'
            else:
                global thread2 #this is a global varible which is the same across all cleints
                with thread2_lock: #locks the global varible so only one client can use it at a time
                    if thread2 is None:
                        thread2=socketio.start_background_task(target=background_thread2)
                        socketio.to('room2').emit('connection2', 'connected')# this is the message that goes along with start in the JQuery code
                        usernum=1
                    usernum=usernum+1
                    print('here2')
        else:
            if session['user_data']['login'] == '':
                yeet='yeet'
            else:
                global thread1 #this is a global varible which is the same across all cleints
                with thread1_lock: #locks the global varible so only one client can use it at a time
                    if thread1 is None:
                        thread1=socketio.start_background_task(target=background_thread1)
                        socketio.to('room1').emit('connection1', 'connected')# this is the message that goes along with start in the JQuery code
                        usernum=1
                    usernum=usernum+1
                    print('here1')
@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

@app.route('/')
def home():
    try:
        print(session['user_data']['login'])
        return render_template('Home.html')
    except:
        return render_template('Home.html')

@app.route('/p3')
def StartGame():
    return render_template('StartGame.html')

@app.route('/p2')
def Info():
    return render_template('Info.html')

@app.route('/login')
def login():
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='http')) #callback URL must match the pre-configured callback URL

@app.route('/logout')
def logout():
    session.clear()
    return render_template('Home.html', message='You were logged out')

@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        message = 'Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args)
    else:
        try:
            session['github_token'] = (resp['access_token'], '') #save the token to prove that the user logged in
            session['user_data']=github.get('user').data
            message='You were successfully logged in as ' + session['user_data']['login']
        except Exception as inst:
            session.clear()
            print(inst)
            message='Unable to login, please try again.  '
    return render_template('Home.html', message=message)

#the tokengetter is automatically called to check who is logged in.
@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')

if __name__ == '__main__':
    os.system("echo json(array) > file")
    app.run()
