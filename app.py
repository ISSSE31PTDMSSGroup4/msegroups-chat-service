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


if use_dynamodb: 
    repo = DynamoMessageRepo()
    friend_repo = FriendRepo()

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

    # print(str(data).replace("'", '"'))

    # We will use the current Unix time as the unique identifier for each message.
    # This will also allow us to sort messages chronologically.
    timestamp = int(round(time.time(),3)*1000)  # Current Unix time
    user = data['user']
    message = data['message']
    user_email = data['userEmail']
    receiver_email = data['receiverEmail']

    channel_name = get_channel_name(user_email, receiver_email)
    
    if use_dynamodb: 
        repo.create(
                    channelName = channel_name,
                    timestamp = timestamp,
                    # User info
                    userId = user['userId'],
                    avatar = user['avatar'],
                    name = user['name'],
                    # Message info
                    message = message,
                    userEmail=user_email,
                    receiverEmail=receiver_email,
                    )

    pusher.trigger(channel_name, 'message', {
            'channelName': channel_name,  # Partition key
            'timestamp': timestamp,  # Sort key
            'user': {
                'userId': user['userId'],
                'name': user['avatar'],
                'avatar': user['name'],
            },
            'message': message,
            'userEmail': user_email,
            'receiverEmail': receiver_email,
        })

    return jsonify({'status': 'success', 'message': 'Operation was successful'}), 200

@app.route('/api/chat/history', methods=['POST'])
def get_history():

    data = request.json

    username = data['userEmail']
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
                    'userId': r['user']["userId"],
                    'name': r['user']["name"],
                    'avatar': r['user']["avatar"],
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

    user_email = data['userEmail']
    
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

    user_email = data['userEmail']
    friend_data = data['friendData']

    friends = []
    if use_dynamodb: 
        friends = friend_repo.add_friend(userEmail=user_email, 
                                         friend_data= friend_data)


    return jsonify([friends])



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
