from flask import Flask, render_template, request, jsonify, make_response, json
from flask_cors import CORS
from pusher import pusher
import simplejson

from messages_repo import MessagesRepo


from messages_repo import MessagesRepo


app = Flask(__name__, template_folder='public')
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


use_local_db = True

# Load the config
with open('config.json', 'r') as config_file:
    config = json.load(config_file)


if use_local_db: repo = MessagesRepo()

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
    print(channel_name)
    return channel_name


@app.route('/api/pusher_config', methods=['GET'])
def get_pusher_config():
    # Return pusher config info
    return jsonify({
        "key": config["server"]["key"],
        "cluster": config["server"]["cluster"]
    })

@app.route('/api/messages', methods=['POST'])
def send_messages():
    data = request.json

    username = data['username']
    receiver = data['receiver']
    time = data['time']

    channel_name = get_channel_name(username , receiver)
    
    if use_local_db: 
        repo.create(channel_name, data['message'],time,sender=username,receiver=receiver)

    pusher.trigger(channel_name, 'message', {
        
        'username' : data['username'],
        'message' : data['message'],
        'time': time
        })

    return jsonify([])

@app.route('/api/history', methods=['POST'])
def get_history():
    data = request.json

    username = data['username']
    receiver = data['receiver']

    channel_name = get_channel_name(username , receiver)

    results = {"results":[]}
    if use_local_db: 
        results = repo.get_all(name=channel_name)["results"]

    messages = []
    print(messages)
    
    if(results): # If there is message history
        for r in results:
            messages.append({
                'username' : r['sender'],
                'message' : r['text'],
                'time': r['time'],
            })

        return jsonify(messages)
    else: # if there is no message history
        return jsonify([])
         


@app.route('/new/guest', methods=['POST'])
def guestUser():
	data = request.json

	pusher.trigger(u'general-channel', u'new-guest-details', {
		'name' : data['name'],
		'email' : data['email']
		})

	return json.dumps(data)


@app.route("/pusher/auth", methods=['POST'])
def pusher_authentication():
	auth = pusher.authenticate(channel=request.form['channel_name'],socket_id=request.form['socket_id'])
	print(json.dumps(auth))
	return json.dumps(auth)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
