import boto3
from boto3.dynamodb.conditions import Key, Attr

class DynamoMessageRepo:
    """Persistence layer abstraction for messages."""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.message_tablename = "MessageTable"
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
            
    def create(self, timestamp, message, userEmail, receiverEmail, channelName, name, userId, avatar):
        """Persist a message to the database."""
        
        if name == "": name = userEmail
        item = {
            'channelName': channelName,  # Partition key
            'timestamp': timestamp,  # Sort key
            'user': {
                'userId': userId,
                'name': name,
                'avatar': avatar
            },
            'message': message,
            'userEmail': userEmail,
            'receiverEmail': receiverEmail,
        }
        
        self.table.put_item(Item=item)
        return item


class FriendRepo:
    """Persistence layer abstraction for friend list and unread messages."""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.friend_tablename = "FriendTable"
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
            return []

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

    def update_last_read(self, userEmail, friend_email, lastReadTime, unread):
        """Update the lastReadTime and unread count for a given friend."""
        current_friends = self.get_all_friends(userEmail)
        for friend in current_friends:
            if friend['email'] == friend_email:
                friend['lastReadTime'] = lastReadTime
                friend['unread'] = unread
                break
        self.table.put_item(Item={'userEmail': userEmail, 'friends': current_friends})

# Example usage:
# repo = FriendRepo()
# repo.add_friend('useEmail1', {...})  # Add a friend to 'useEmail1'
# repo.update_last_read('useEmail1', '1@gmail.com', 200, 0)  # Update lastReadTime and unread count for '1@gmail.com'