import boto3
from boto3.dynamodb.conditions import Key, Attr

class DynamoMessageRepo:
    """Persistence layer abstraction for messages."""
    
    def __init__(self,aws_access_key_id,aws_secret_access_key,aws_region_name):
        self.dynamodb = boto3.resource(
                'dynamodb',
                region_name=aws_region_name,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )
        self.message_tablename = "MessageTable_test2"
        self.table = self.dynamodb.Table(self.message_tablename)
        self._ensure_table_exists(self.message_tablename)
        
    def _ensure_table_exists(self, table_name):
        """Ensure the DynamoDB table exists. Create it if required."""
        existing_tables = self.dynamodb.meta.client.list_tables()['TableNames']
        if table_name not in existing_tables:
            self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'channelName', 'KeyType': 'HASH'},  # Partition key
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}  # Sort key
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'channelName', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'N'}  # 'N' for number. Unix time is a numeric value.
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 15,
                    'WriteCapacityUnits': 15
                }
            )
        
    def get_all(self, channelName, after_timestamp=0):
        """Get all of the existing messages."""
        response = self.table.query(
            KeyConditionExpression=Key('channelName').eq(channelName) & Key('timestamp').gt(after_timestamp)
        )
        return {'results': response['Items']}
            
    def create(self, timestamp, message, userEmail, receiverEmail, channelName, userInfo, receiverInfo):
        """Persist a message to the database."""
        
        item = {
            'channelName': channelName,  # Partition key
            'timestamp': timestamp,  # Sort key
            'message': message,
            'userEmail': userEmail,
            'receiverEmail': receiverEmail,
            'userInfo': userInfo,
            'receiverInfo': receiverInfo
        }
        
        self.table.put_item(Item=item)
        return item

class FriendRepo:
    """Persistence layer abstraction for friend list and unread messages."""
    
    def __init__(self,aws_access_key_id,aws_secret_access_key,aws_region_name):
        self.dynamodb = boto3.resource(
                'dynamodb',
                region_name=aws_region_name,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )        
        self.friend_tablename = "FriendTable6"
        self.table = self.dynamodb.Table(self.friend_tablename)
        self._ensure_table_exists(self.friend_tablename)
        
    def _ensure_table_exists(self, table_name):
        """Ensure the DynamoDB table exists. Create it if required."""
        existing_tables = self.dynamodb.meta.client.list_tables()['TableNames']
        if table_name not in existing_tables:
            self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'userEmail', 'KeyType': 'HASH'},  # Partition key
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'userEmail', 'AttributeType': 'S'},
                    # {'AttributeName': 'currentChatFriend', 'AttributeType': 'S'},
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
            )

    def get_all_friends(self, userEmail):
        """Get all of the friends for a given user."""
        response = self.table.get_item(Key={'userEmail': userEmail})
        if 'Item' in response:
            return response['Item']  
        else: # If the user does not have friends, create a new entry for him / her.
            self.table.put_item(Item={'userEmail': userEmail, 'friends': []})
            return {'userEmail': userEmail, 'friends': []}

    def add_friend(self, userEmail, friend_data):
        """Add a new friend to the user's friend list."""
        current_friends = self.get_all_friends(userEmail)["friends"]

        if current_friends == []:
            current_friends.append(friend_data)
            self.table.put_item(Item={'userEmail': userEmail, 'friends': current_friends})
        else:
            friend_email = friend_data.get('email')

            # Remove the old friend data if it exists
            updated_friends = [friend for friend in current_friends if friend.get('email') != friend_email]

            # Append the new friend data
            updated_friends.append(friend_data)

            # Update the database item
            self.table.update_item(
                Key={'userEmail': userEmail},
                UpdateExpression="set friends = :f",
                ExpressionAttributeValues={
                    ':f': updated_friends
                },
                ReturnValues="UPDATED_NEW"
            )

    def add_unread(self, userEmail, friendEmail):
        """Update the lastReadTime and unread count for a given friend."""
        current_friends = self.get_all_friends(userEmail)["friends"]
        for friend in current_friends:
            if friend['email'] == friendEmail:
                if "unread" not in friend or type(friend['unread']) != int or type(friend['unread']) != float:
                    friend['unread'] = 1
                else:
                    friend['unread'] += 1
                break
        self.table.update_item(
                Key={
                    'userEmail': userEmail  # Partition key
                },
                UpdateExpression="SET friends = :f",
                ExpressionAttributeValues={
                    ':f': current_friends
                },
                ReturnValues="UPDATED_NEW"
            )
    
    def clear_unread(self, userEmail, friend_email):
        """Update the lastReadTime and unread count for a given friend."""
        current_friends = self.get_all_friends(userEmail)["friends"]
        for friend in current_friends:
            if friend['email'] == friend_email:
                friend['unread'] = 0
                break
        self.table.update_item(
                Key={
                    'userEmail': userEmail  # Partition key
                },
                UpdateExpression="SET friends = :f",
                ExpressionAttributeValues={
                    ':f': current_friends
                },
                ReturnValues="UPDATED_NEW"
            )

    def update_current_chat(self, userEmail, currentChatFriend):
        """Update the last chat frind for a given user ."""
        self.table.update_item(
                Key={
                    'userEmail': userEmail  # Partition key
                },
                UpdateExpression="SET currentChatFriend = :f",
                ExpressionAttributeValues={
                    ':f': currentChatFriend
                },
                ReturnValues="UPDATED_NEW"
            )

    def get_current_chat(self,userEmail):
        """Get the last chat friend for a given user ."""
        current_friends = self.get_all_friends(userEmail)
        if current_friends and "currentChatFriend" in current_friends:
            return current_friends["currentChatFriend"]
        else:
            return None

# Example usage:
# repo = FriendRepo()
# repo.add_friend('useEmail1', {...})  # Add a friend to 'useEmail1'
# repo.update_last_read('useEmail1', '1@gmail.com', 200, 0)  # Update lastReadTime and unread count for '1@gmail.com'