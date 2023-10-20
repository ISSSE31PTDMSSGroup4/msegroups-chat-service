from flask import Flask, render_template, request, jsonify, make_response, json
from flask_cors import CORS
from pusher import pusher
import simplejson
import time

# from messages_repo import MessagesRepo

from dynamodb_ropo import DynamoMessageRepo,FriendRepo

app = Flask(__name__, template_folder='public')
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


# use_local_db = True
use_dynamodb = True

# Load the config
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

aws_access_key_id = config["aws"]["aws_access_key_id"]
aws_secret_access_key = config["aws"]["aws_secret_access_key"]
aws_region_name = config["aws"]["aws_region_name"]

if use_dynamodb: 
    repo = DynamoMessageRepo(aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key = aws_secret_access_key,
                            aws_region_name=aws_region_name)
    
    friend_repo = FriendRepo(aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key = aws_secret_access_key,
                            aws_region_name=aws_region_name)

# Use the config to initialize Pusher
pusher = pusher_client = pusher.Pusher(
  app_id=config["server"]["app_id"],
  key=config["server"]["key"],
  secret=config["server"]["secret"],
  cluster=config["server"]["cluster"],
  ssl=True
)

def get_channel_name(username1, username2):
    # Sort the usernames
    sorted_usernames = sorted([username1, username2])

    # Join with a delimiter
    channel_name = sorted_usernames[0] + "-" + sorted_usernames[1]
    return channel_name

@app.route('/api/chat/config', methods=['GET'])
def get_pusher_config():
    # Return pusher config info
    return jsonify({
        "key": config["server"]["key"],
        "cluster": config["server"]["cluster"]
    })

@app.route('/api/chat/message', methods=['POST'])
def send_messages():
    data = request.json

    
    # We will use the current Unix time as the unique identifier for each message.
    # This will also allow us to sort messages chronologically.
    timestamp = int(round(time.time(),3)*1000)  # Current Unix time
    message = data['message']
    
    x_user = request.headers.get('X-User')
    if x_user is None: user_email = data['userEmail']
    else: user_email = x_user

    receiver_email = data['receiverEmail']

    user_info = data['userInfo']
    receiver_info = data["receiverInfo"]

    channel_name = get_channel_name(user_email, receiver_email)
    
    if use_dynamodb: 
        repo.create(
                    channelName = channel_name,
                    timestamp = timestamp,
                    message = message,
                    userEmail=user_email,
                    receiverEmail=receiver_email,
                    userInfo= user_info, # User info
                    receiverInfo= receiver_info # Receiver info
                    )

    # Trigger the 'message' event for the 'chat' channel
    # In chat case, channel_name is the combination of two users' email
    pusher.trigger(channel_name, 'message', {
            'channelName': channel_name,  # Partition key
            'timestamp': timestamp,  # Sort key
            'userInfo': {
                'userId': user_info['userId'],
                'name': user_info['avatar'],
                'avatar': user_info['name'],
            },
            'receiverInfo': {  
                'userId': receiver_info['userId'],
                'name': receiver_info['avatar'],
                'avatar': receiver_info['name'],
            },
            'message': message,
            'userEmail': user_email,
            'receiverEmail': receiver_email,
        })

    return jsonify({'status': 'success', 'message': 'Operation was successful'}), 200

@app.route('/api/chat/history', methods=['POST'])
def get_history():

    data = request.json
    x_user = request.headers.get('X-User')

    if x_user is None: username = data['userEmail']
    else: username = x_user
    receiver = data['receiverEmail']

    channel_name = get_channel_name(username , receiver)

    results = {"results":[]}
    if use_dynamodb: 
        results = repo.get_all(channelName=channel_name)["results"]

    messages = []
    
    if(results): # If there is message history
        for r in results:
            messages.append({
                'channelName': r["channelName"],  # Partition key
                'timestamp': int(r["timestamp"]),  # Sort key
                'user': {
                    'userId': r['userInfo']["userId"],
                    'name': r['userInfo']["name"],
                    'avatar': r['userInfo']["avatar"],
                }, 
                'receiverInfo': {  
                    'userId': r['receiverInfo']['userId'],
                    'name': r['receiverInfo']['avatar'],
                    'avatar': r['receiverInfo']['name'],
                },
                'message': r["message"],
                'userEmail': r["userEmail"],
                'receiverEmail': r["receiverEmail"],
            })

        return jsonify(messages)
    else: # if there is no message history
        return jsonify([])
    
@app.route('/api/chat/friendlist', methods=['POST'])
def get_friend_list():
    data = request.json

    x_user = request.headers.get('X-User')
    if x_user is None: user_email = data['userEmail']
    else: user_email = x_user

    results = []
    if use_dynamodb: 
        results = friend_repo.get_all_friends(userEmail=user_email)
    
    if results != []:
        return jsonify(results["friends"])
    else:
        return jsonify([])

@app.route('/api/chat/addfriend', methods=['POST'])
def add_friend():
    data = request.json

    x_user = request.headers.get('X-User')
    if x_user is None: user_email = data['userEmail']
    else: user_email = x_user
    user_data = data['userData']

    friend_data = data['friendData']
    friend_email = friend_data['email']

    if use_dynamodb: 
        friend_repo.add_friend(userEmail=user_email, 
                                         friend_data= friend_data)
        friend_repo.add_friend(userEmail=friend_email, 
                                         friend_data= user_data)
    
    channel_name = user_email
    # Add rquester to the friend's friend list and update UI accordingly
    pusher.trigger(channel_name, 'newfriend', {
            'channelName': channel_name,
            'userData': user_data 
        })

    return jsonify([])


@app.route('/api/chat/addfriend-multi', methods=['POST'])
def add_multi_friend():

    x_user = request.headers.get('X-User')
    if x_user is None: user_email = request.json['userEmail']
    else: user_email = x_user
    user_data = request.json['userData']

    friend_data = request.json["friendData"]

    for friend_data in request.json["friendData"]:
        if use_dynamodb: 
            friend_email = friend_data['email']
            friend_repo.add_friend(userEmail=user_email, 
                                            friend_data= friend_data)
            friend_repo.add_friend(userEmail=friend_email, 
                                            friend_data= user_data)
        
            channel_name = user_email
            # Add rquester to the friend's
            #  friend list and update UI accordingly
            pusher.trigger(channel_name, 'newfriend', {
                    'channelName': channel_name,
                    'userData': user_data 
                })

    return jsonify([])



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
