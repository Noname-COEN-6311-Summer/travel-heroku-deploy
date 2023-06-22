import glob
import sqlite3
import os
from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from datetime import datetime
import stripe
import json
from models import Package
from controllers import BookManager

app = Flask(__name__)
app.secret_key = os.urandom(24)
stripe.api_key = 'sk_test_51NKDyyBhv3RRjKlwPulSQ7QH4cAcqm8EWVbFLQ45lBLrUrrrGciSgO8ob3rUUKInhtCD51NWGUSoN4aZlxWTPZv000IAjZeXq0'

class Customer:
    def __init__(self):
        self.database_folder = None
        self.agent = Agent()
        self.username = None
        self.db_name = None

    def search_destination(self, query):
        query = query.lower()
        if query in self.agent.packages:
            return f'/{query}.html'
        return None

    def modify_package(self, destination, hotel, flights, activities, departure):
        package = self.agent.get_packages(destination)
        if package:
            package.hotel = hotel
            package.flights = flights
            package.activities = activities
            package.departure = departure
            return True
        return False

    def edit_profile(self, username):
        # self.username = username  # Store the logged-in username
        self.database_folder = "database"
        self.db_name = f"{self.database_folder}/{username}_bookings.db"

    def get_profile(self):
        if self.username:
            username = self.username  # Store the username in a local variable
            # Fetch the user profile details from the database based on the stored username
            connection = sqlite3.connect('database/accounts.db')
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM accounts WHERE username=?', (username,))
            profile = cursor.fetchone()
            cursor.close()
            connection.close()
            return profile
        return None

    def book_package(self, destination):
        package = self.agent.get_packages(destination)
        if package:
            # Store the booking information in the database
            self.agent.store_package(package)
            return True
        return False

    def get_bookings(self):
        connection = sqlite3.connect('database/bookings.db')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM bookings')
        rows = cursor.fetchall()
        cursor.close()
        connection.close()

        bookings = []
        for row in rows:
            destination = row[1]
            hotel = row[2]
            flights = row[3]
            activities = row[4]
            departure = row[5]
            price = row[6]
            package = Package(destination, hotel, flights, activities, departure, price)
            bookings.append(package)

        return bookings

    def get_book_information(self):
        return BookManager(self.username)

    def cancel_booking(self, booking_id):
        if self.username is None:
            return []

        database_folder = "database"
        # db_name = f"{database_folder}/{self.username}_bookings.db"

        connection = sqlite3.connect(f"{database_folder}/{self.username}_bookings.db")
        cursor = connection.cursor()
        cursor.execute('DELETE FROM bookings WHERE id=?', (booking_id,))
        connection.commit()
        cursor.close()
        connection.close()

        book_manager = BookManager(self.username)
        bookings = book_manager.get_bookings()
        return bookings

    def pay_booking(self, booking_id):
        pass

    def register(self, username, password, favorite_color):
        account_manager = AccountManager()
        account_manager.register(username, password, favorite_color)

    def login(self, username, password):
        account_manager = AccountManager()
        return account_manager.login(username, password)

    def logout(self):
        account_manager = AccountManager()
        account_manager.logout()

    def reset_password(self, username, new_password):
        account_manager = AccountManager()
        account_manager.reset_password(username, new_password)

    def send_message(self, recipient, content):
        message = Message(self.username, recipient, content)
        self.agent.receive_message(message)
        self.store_message(message)

    def store_message(self, message):
        connection = sqlite3.connect('database/messages.db')
        cursor = connection.cursor()
        cursor.execute('INSERT INTO messages (sender, recipient, content, timestamp) VALUES (?, ?, ?, ?)',
                       (message.sender, message.recipient, message.content, message.timestamp))
        connection.commit()
        cursor.close()
        connection.close()

    def get_messages(self, username):
        connection = sqlite3.connect('database/messages.db')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM messages WHERE sender=? OR recipient=?', (username, username))
        rows = cursor.fetchall()
        cursor.close()
        connection.close()

        messages = []
        for row in rows:
            sender = row[1]
            recipient = row[2]
            content = row[3]
            timestamp = row[4]
            message = Message(sender, recipient, content)
            message.timestamp = timestamp
            messages.append(message)

        return messages
