
import unittest
from app import app
from unittest.mock import patch, MagicMock

class ChatAppTestCase(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('app.pusher_client.authenticate')
    def test_pusher_authentication(self, mock_authenticate):
        mock_authenticate.return_value = {'auth': 'test_auth_token'}

        response = self.app.post('/api/chat/auth/', data={
            'email': 'user@example.com',
            'channel_name': 'test_channel',
            'socket_id': '12345'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('test_auth_token', response.json['auth'])

    def test_get_pusher_config(self):
        response = self.app.get('/api/chat/config/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('key', response.json)
        self.assertIn('cluster', response.json)

    @patch('app.pusher.trigger')
    @patch('app.DynamoMessageRepo.create')
    def test_send_messages(self, mock_repo_create, mock_pusher_trigger):
        mock_pusher_trigger.return_value = None
        mock_repo_create.return_value = None

        response = self.app.post('/api/chat/message/', json={
            'message': 'Hello',
            'userEmail': 'sender@example.com',
            'receiverEmail': 'receiver@example.com',
            'userInfo': {'name': 'Sender'},
            'receiverInfo': {'name': 'Receiver',}
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'success')

    @patch('app.DynamoMessageRepo.get_all')
    def test_get_history(self, mock_get_all):
        mock_get_all.return_value = {"results": []} 

        response = self.app.post('/api/chat/history/', json={
            'userEmail': 'user@example.com',
            'receiverEmail': 'receiver@example.com'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [])

    @patch('app.FriendRepo.get_all_friends')
    def test_get_friend_list(self, mock_get_all_friends):
        mock_get_all_friends.return_value = {"friends": []}  

        response = self.app.post('/api/chat/friendlist/', json={'userEmail': 'user@example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [])


    @patch('app.pusher.trigger')
    @patch('app.FriendRepo.add_friend')
    def test_add_friend(self, mock_add_friend, mock_pusher_trigger):
        mock_add_friend.return_value = None
        mock_pusher_trigger.return_value = None

        response = self.app.post('/api/chat/addfriend/', json={
            'userEmail': 'user@example.com',
            'userData': {'name': 'User'},
            'friendData': {'email': 'friend@example.com', 'name': 'Friend'}
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [])


    @patch('app.pusher.trigger')
    @patch('app.FriendRepo.add_friend')
    def test_add_multi_friend(self, mock_add_friend, mock_pusher_trigger):
        mock_add_friend.return_value = None
        mock_pusher_trigger.return_value = None

        response = self.app.post('/api/chat/addfriend-multi/', json={
            'userEmail': 'user@example.com',
            'userData': {'name': 'User'},
            'friendData': [{'email': 'friend1@example.com', 'name': 'Friend1'}, {'email': 'friend2@example.com', 'name': 'Friend2'}]
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [])


    @patch('app.FriendRepo.update_current_chat')
    def test_update_last_chat(self, mock_update_current_chat):
        mock_update_current_chat.return_value = None

        response = self.app.post('/api/chat/lastchat/', json={
            'userEmail': 'user@example.com',
            'receiverEmail': 'receiver@example.com'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [])

    @patch('app.FriendRepo.update_friend_data_for_others')
    def test_update_user_info(self, mock_update_friend_data_for_others):
        mock_update_friend_data_for_others.return_value = None

        response = self.app.post('/api/chat/updateuser/', json={
            'userEmail': 'user@example.com',
            'newData': {'name': 'Updated User'}
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'success', 'message': 'User data updated successfully'})

    