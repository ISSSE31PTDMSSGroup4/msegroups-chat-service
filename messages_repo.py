# -*- coding: utf-8 -*-

import sqlite3
import time

class MessagesRepo:
    """Persistence layer abstraction for messages."""
    
    def __init__(self):
        self._ensure_table_exists()
        
    def _connect(self):
        return sqlite3.connect('messages.db')
    
    def _ensure_table_exists(self):
        """Create the sqlite3 DB, if requred."""
        try:
            db = self._connect()
            cursor = db.cursor()
            cursor.execute( ''' 
                            create table if not exists messages
                            (id INTEGER PRIMARY KEY, name TEXT, 
                            text TEXT, time TEXT, message_id INTEGER,
                           sender TEXT, receiver TEXT)
                            ''')  #name used here is the channel name instead of sender / reciever name 
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            
    def _row_to_status_dict(self, row):
        """Convert a row into a dict for easier consumption"""
        return {
            'id': row[0],
            'name': row[1],
            'text': row[2],
            'time': row[3],
            "message_id": row[4],
            "sender": row[5],
            "receiver": row[6]
        }
            
    def get_all(self, name, after_id=0):
        """Get all of the existing messages"""
        try:
            db = self._connect()
            cursor = db.cursor()
            
            cursor.execute('''SELECT * FROM messages WHERE name == ? AND message_id > ?''', (name ,after_id))
                
            all_rows = cursor.fetchall()
            
            all = []
            for row in all_rows:
                all.append(self._row_to_status_dict(row))
        
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
        
        return {'results': all}

    def get_messages_count(self, name):
        count = 0
        try:
            db = self._connect()
            cursor = db.cursor()

            cursor.execute('''SELECT COUNT(*) FROM messages WHERE name == ?''', (name,))
            count = cursor.fetchone()[0]  

            db.commit()

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
        return count
            
    def create(self, name, text, time, sender, receiver):
        """Persist a message to the database"""
        
        message = None
        
        try:
            db = self._connect()
            cursor = db.cursor()
            
            message_id = self.get_messages_count(name)

            cursor.execute('''INSERT INTO messages(name, text, time, message_id, sender, receiver)
                  VALUES(?,?,?,?,?,?)''', (name, text, time, message_id, sender, receiver))
            
            message = self._row_to_status_dict([
                cursor.lastrowid,
                name,
                text,
                time,
                message_id,
                sender,
                receiver
            ])

            db.commit()

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            
        return message
