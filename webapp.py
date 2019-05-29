
from flask import Flask, redirect, url_for, session, request, jsonify, Markup, render_template
from flask_oauthlib.client import OAuth
from time import localtime, strftime
from bson.objectid import ObjectId
from threading import Lock
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect

#===============================================================================

import pprint
import os
import json
import pymongo
import dns
import sys

#===============================================================================

app = Flask(__name__)
socketio = SocketIO(app, async_mode=None)
usernum=0
thread1 = None
usernum_lock=Lock()
thread1_lock = Lock()
thread2 = None
thread2_lock = Lock()

play1 = None
play1_lock = Lock()
play2 = None
play2_lock = Lock()
var=False
var_lock = Lock()

client1=None
client2=None
#===============================================================================

app.debug = True #Change this to False for production
app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)

#===============================================================================

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

#===============================================================================

def background_thread1():
    count=0
    while True:
        socketio.sleep(5) #wait 5 seconds
        count=count+1
        socketio.emit('count_event1', count) #sends out the varible count to all of the cleints

#===============================================================================


url = 'mongodb://{}:{}@{}/{}'.format(
    os.environ["MONGO_USERNAME"],
    os.environ["MONGO_PASSWORD"],
    os.environ["MONGO_HOST"],
    #os.environ["MONGO_PORT"],
     os.environ["MONGO_DBNAME"])
#mongodb+srv://admin:<password>@cluster0-oe70w.mongodb.net/test?retryWrites=true
client = pymongo.MongoClient(os.environ["MONGO_HOST"])
db = client[os.environ["MONGO_DBNAME"]]
collection = db['scores'] #put the name of your collection in the quotes



def database():
    if session['user_data']['login'] != '':
        if not collection.find_one({session['user_data']['login']:{'$gt':-1}}) == None:
            return collection.find_one({session['user_data']['login']:{'$gt':-1}})[session['user_data']['login']]
        else:
            collection.insert_one({session['user_data']['login']: 0})
            print('x')
            return 0






def background_thread2():

    count=0
    while True:
        socketio.sleep(5) #wait 5 seconds
        count=count+1
        #collection.update({session['user_data']['login']: database()}, {'$set':{session['user_data']['login']: database() + count}})
        socketio.emit('count_event2', count) #sends out the varible count to all of the cleints
        socketio.emit('count_event', count) #sends out the varible count to all of the cleints



         # if client 1 = 'Rock' and client 2 = 'Paper': print client 2 won



        #win=request.form["Rock"] win=request.form["Paper"] win=request.form["Scissors"]

#===============================================================================

#this code littarly efects nothing feel free to delete but may need in future

@socketio.on('connect')
def test_connect():
    global usernum
    with usernum_lock:
        print(usernum)
        if usernum <= 2:
            if session['user_data']['login'] == '':
                yeet='yeet'
            else:
                global thread2 #this is a global varible which is the same across all cleints
                with thread2_lock: #locks the global varible so only one client can use it at a time
                    if thread2 is None:
                        thread2=socketio.start_background_task(target=background_thread2)
                        socketio.to('room2').emit('connection2', 'connected')# this is the message that goes along with start in the JQuery code
                    usernum=usernum+1
                    print('function 2')

#===============================================================================

@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

#===============================================================================

@app.route('/')
def home():
    try:
        print(session['user_data']['login'])
        return render_template('Home.html')
    except:
        return render_template('Home.html')

#===============================================================================

@app.route('/p3')
def StartGame(response=""):
    if 'user_data' not in session:
        return render_template('StartGame.html')
    else:
        #if not collection.find_one({session['user_data']['login']:{'$gt':-1}}) == None:
            #collection.update({session['user_data']['login']: database()}, {'$set':{session['user_data']['login']: database() + 1}})
        if "response" in session:
            temp= session["response"]
            session["response"]=' '
            return render_template('StartGame.html', username = session['user_data']['login'], score = database(), sen = temp)
        return render_template('StartGame.html', username = session['user_data']['login'], score = database(), sen = response)

#===============================================================================

@app.route('/button', methods=['POST'])
def Button():
    global client1
    global client2
    global var
    global test

    if 'Rock' in request.form:
        print("rock")
        buttonpressed='True'
    if 'Paper'in request.form:
        print("paper")
        buttonpressed='True'
    if 'Scissors' in request.form:
        print("scissors")


    test = False 


    with var_lock:

        if var == False:
            global play1
            with play1_lock:
                client1=session['user_data']['login']
                if play1 is None and 'Rock' in request.form:
                    play1= request.form['Rock']
                    print("rock played")
                if play1 is None and 'Paper' in request.form:
                    play1= request.form['Paper']
                    print("paper played")
                if play1 is None and 'Scissors' in request.form:
                    play1= request.form['Scissors']
                    print("scissors played")
                var= True
                test= True
                print(var)
        else:
            global play2
            with play2_lock:
                client2=session['user_data']['login']
                if play2 is None and 'Rock' in request.form:
                    play2= request.form['Rock']
                    print("rock played2")
                if play2 is None and 'Paper' in request.form:
                    play2= request.form['Paper']
                    print("paper played2")
                if play2 is None and 'Scissors' in request.form:
                    play2= request.form['Scissors']
                    print("scissors played2")
                    test = True
                    
    session["response"]=' '
    if play1 == 'Rock' and play2 == 'Paper':
        print('client 2 won')
        var=False
        play1=None
        play2=None
        usernum=0
        session["response"]=client2 +' won'
        collection.update({client2: database()}, {'$set':{client2: database() + 10}})
        if collection.find_one({client1:{'$gt':-1}})[client1] >= 5:
            collection.update({client1: database()}, {'$set':{client1: database() - 5}})
        else:
            collection.update({client1: database()}, {'$set':{client1: 0}})
        client1=None
        client2=None
        test = False
    if play1 == 'Paper' and play2 == 'Rock':
        print ('client 1 won')
        var=False
        play1=None
        play2=None
        usernum=0
        session["response"]= client1 + ' won'
        collection.update({client1: database()}, {'$set':{client1: database() + 10}})
        if collection.find_one({client2:{'$gt':-1}})[client2] >= 5:
            collection.update({client2: database()}, {'$set':{client2: database() - 5}})
        else:
            collection.update({client2: database()}, {'$set':{client2: 0}})
        client1=None
        client2=None
        test = False
    if play1 == 'Scissors' and play2 == 'Paper':
        print ('client 1 won')
        var=False
        play1=None
        play2=None
        usernum=0
        session["response"]=client1 + ' won'
        collection.update({client1: database()}, {'$set':{client1: database() + 10}})
        if collection.find_one({client2:{'$gt':-1}})[client2] >= 5:
            collection.update({client2: database()}, {'$set':{client2: database() - 5}})
        else:
            collection.update({client2: database()}, {'$set':{client2: 0}})
        client1=None
        client2=None
        test = False
    if play1  == 'Paper' and play2  == 'Scissors':
        print ('client 2 won')
        var=False
        play1=None
        play2=None
        usernum=0
        session["response"]=client2 +  'won'
        collection.update({client2: database()}, {'$set':{client2: database() + 10}})
        if collection.find_one({client1:{'$gt':-1}})[client1] >= 5:
            collection.update({client1: database()}, {'$set':{client1: database() - 5}})
        else:
            collection.update({client1: database()}, {'$set':{client1: 0}})
        client1=None
        client2=None
        test = False
    if play1  == 'Rock' and play2  == 'Scissors':
        print ('client 1 won')
        var=False
        play1=None
        play2=None
        usernum=0
        session["response"]=client1 + 'won'
        collection.update({client1: database()}, {'$set':{client1: database() + 10}})
        if collection.find_one({client2:{'$gt':-1}})[client2] >= 5:
            collection.update({client2: database()}, {'$set':{client2: database() - 5}})
        else:
            collection.update({client2: database()}, {'$set':{client2: 0}})
        client1=None
        client2=None
        test = False
    if play1  == 'Scissors' and play2  == 'Rock':
        print('client 2 won')
        var=False
        play1=None
        play2=None
        usernum=0
        session["response"]==client2 + 'won'
        collection.update({client2: database()}, {'$set':{client2: database() + 10}})
        if collection.find_one({client1:{'$gt':-1}})[client1] >= 5:
            collection.update({client1: database()}, {'$set':{client1: database() - 5}})
        else:
            collection.update({client1: database()}, {'$set':{client1: 0}})
        client1=None
        client2=None
        test = False
    if play1  == 'Scissors' and play2  == 'Scissors':
        print('tie')
        var=False
        play1=None
        play2=None
        usernum=0
        session["response"]='The game was a tie'
        collection.update({client2: database()}, {'$set':{client2: database() + 2}})
        collection.update({client1: database()}, {'$set':{client1: database() + 2}})
        client1=None
        client2=None
        test = False
    if play1  =='Rock' and play2  == 'Rock':
        print('tie')
        var=False
        play1=None
        play2=None
        usernum=0
        session["response"]='The game was a tie'
        collection.update({client2: database()}, {'$set':{client2: database() + 2}})
        collection.update({client1: database()}, {'$set':{client1: database() + 2}})
        client1=None
        client2=None
        test = False
    if play1  == 'Paper' and play2  == 'Paper':
        print('tie')
        var=False
        play1=None
        play2=None
        usernum=0
        client1=None
        client2=None  
        session["response"]='The game was a tie'
        collection.update({client2: database()}, {'$set':{client2: database() + 2}})
        collection.update({client1: database()}, {'$set':{client1: database() + 2}})
        client1=None
        client2=None
        test = False
    print(var)
    return redirect(url_for("StartGame"))

#===============================================================================

@app.route('/p2')
def Info():
    if 'user_data' not in session:
        return render_template('Info.html')
    else:
        x2 = 0
        x3 = 0
        x4 = 0
        x5 = 0
        i2 = ""
        i3 = ""
        i4 = ""
        y = 0
        z = ""
        for i in collection.find():
            for x in i:
                if x2 == 0:
                    if not x == "_id":
                        print(i[x])
                        x3 = i[x]
                        i2 = x
                else:
                    if not x == "_id":
                        print(x)
                        print(i[x])
                        if i[x] > x3:
                            x3 = i[x]
                            i2 = x
                x2 = 1
        x2 = 0
        for i in collection.find():
            for x in i:
                if x2 == 0:
                    if not x == "_id":
                        print(i[x])
                        y = i[x]
                        z = x
                else:
                    if not x == "_id":
                        print(x)
                        print(i[x])
                        if not i2 == x and i[x] <= x3 and i[x] > x4:
                            x4 = i[x]
                            i3 = x
                        if not z == x and y <= x3 and y > x4:
                            x4 = y
                            i3 = z
                x2 = 1
        x2 = 0
        for i in collection.find():
            for x in i:
                if x2 == 0:
                    if not x == "_id":
                        print(i[x])
                        y = i[x]
                        z = x
                else:
                    if not x == "_id":
                        print(x)
                        print(i[x])
                        if not i2 == x and not i3 == x and i[x] <= x4 and i[x] > x5:
                            x5 = i[x]
                            i4 = x
                        if not z == x and y <= x4 and y > x5:
                            x5 = y
                            i4 = z
                x2 = 1
        return render_template('Info.html', username1 = i2, username2 = i3, username3 = i4, score1 = x3, score2 = x4, score3 = x5)


#===============================================================================

@app.route('/login')
def login():
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='http')) #callback URL must match the pre-configured callback URL

#===============================================================================

@app.route('/logout')
def logout():
    session.clear()
    return render_template('Home.html', message='You were logged out')

#===============================================================================

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

#===============================================================================

#the tokengetter is automatically called to check who is logged in.
@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')

#===============================================================================

if __name__ == '__main__':
    os.system("echo json(array) > file")
    app.run()
