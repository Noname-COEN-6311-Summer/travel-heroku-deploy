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

class BookManager:
    def __init__(self, username):
        self.username = username
        self.db_name = f'{self.username}_bookings.db'
        self.create_table()

    def create_table(self):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                destination TEXT,
                hotel TEXT,
                flights TEXT,
                activities TEXT,
                departure TEXT,
                price INTEGER
            )
        ''')
        connection.commit()
        cursor.close()
        connection.close()

    def store_booking(self, package):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute('''
            INSERT INTO bookings (destination, hotel, flights, activities, departure, price)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            package.destination, package.hotel, package.flights, package.activities, package.departure, package.price))
        connection.commit()
        cursor.close()
        connection.close()

    def get_bookings(self):
        connection = sqlite3.connect(f'{self.username}_bookings.db')
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