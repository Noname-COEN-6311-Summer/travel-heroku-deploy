import glob
import sqlite3
import os
from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from datetime import datetime
import stripe
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)
stripe.api_key = 'sk_test_51NKDyyBhv3RRjKlwPulSQ7QH4cAcqm8EWVbFLQ45lBLrUrrrGciSgO8ob3rUUKInhtCD51NWGUSoN4aZlxWTPZv000IAjZeXq0'

class AccountManager:
    def __init__(self):
        self.create_table()
        self.agentaccounts()

    def create_table(self):
        connection = sqlite3.connect('accounts.db')
        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                favorite_color TEXT,
                consecutive_failures INTEGER DEFAULT 0
            )
        ''')
        connection.commit()
        cursor.close()
        connection.close()

    def register(self, username, password, favorite_color):
        connection = sqlite3.connect('accounts.db')
        cursor = connection.cursor()
        cursor.execute('INSERT INTO accounts (username, password, favorite_color) VALUES (?, ?, ?)',
                       (username, password, favorite_color))
        connection.commit()
        cursor.close()
        connection.close()

    def login(self, username, password):
        connection = sqlite3.connect('accounts.db')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM accounts WHERE username=?', (username,))
        account = cursor.fetchone()

        if account and account[2] == password:  # Check if the password is correct
            session['logged_in'] = True
            cursor.close()
            connection.close()
            return True

        cursor.close()
        connection.close()
        session['logged_in'] = False
        return False

    def logout(self):
        session.pop('logged_in', None)

    def agentaccounts(self):
        # Add agent account data to the 'accounts' table in the 'agent.db' database
        connection = sqlite3.connect('accounts.db')
        cursor = connection.cursor()

        agent_accounts = [
            ('DiWang', '123456', 'blue'),
            ('Melika', '1234567', 'red'),
        ]

        for username, password, favorite_color in agent_accounts:
            cursor.execute('SELECT * FROM accounts WHERE username=?', (username,))
            existing_account = cursor.fetchone()
            if existing_account is None:
                cursor.execute('INSERT INTO accounts (username, password, favorite_color) VALUES (?, ?, ?)', (username, password, favorite_color))

        connection.commit()
        cursor.close()
        connection.close()

    def account_security(self, username, new_password=None):
        connection = sqlite3.connect('accounts.db')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM accounts WHERE username=?', (username,))
        account = cursor.fetchone()

        if account:
            if new_password:  # Check if a new password is provided for password reset
                cursor.execute('UPDATE accounts SET password=? WHERE username=?', (new_password, username))
                connection.commit()
                cursor.close()
                connection.close()
                return None
            else:
                return 'Please reset your password.'

        cursor.close()
        connection.close()
        return None

    def check_security_answer(self, username, security_answer):
        connection = sqlite3.connect('accounts.db')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM accounts WHERE username=? AND favorite_color=?',
                       (username, security_answer))
        account = cursor.fetchone()
        cursor.close()
        connection.close()
        return account is not None

    def reset_password(self, username, new_password):
        connection = sqlite3.connect('accounts.db')
        cursor = connection.cursor()
        cursor.execute('UPDATE accounts SET password=? WHERE username=?', (new_password, username))
        connection.commit()
        cursor.close()
        connection.close()

account_manager = AccountManager()