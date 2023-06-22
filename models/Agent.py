import glob
import sqlite3
import os
from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from datetime import datetime
import stripe
import json
from controllers import BookManager
import Package, Customer, Message

app = Flask(__name__)
app.secret_key = os.urandom(24)
stripe.api_key = 'sk_test_51NKDyyBhv3RRjKlwPulSQ7QH4cAcqm8EWVbFLQ45lBLrUrrrGciSgO8ob3rUUKInhtCD51NWGUSoN4aZlxWTPZv000IAjZeXq0'


class Agent:
    def __init__(self):
        self.packages = {
            'iceland': Package('Iceland', 'Lagoon', 'Air Canada', 'Excursions', '6am 07/05/23', 2100),
            'greece': Package('Greece', 'Westin', 'Air Canada', 'Food Tour', '6am 07/05/23', 2000),
            'banff': Package('Banff', 'Fairmont', 'Air Canada', 'Guided Tour', '6am 07/05/23', 1900),
        }
        self.create_table()

    def get_packages(self, destination):
        return self.packages.get(destination)

    def represent_packages(self, destination):
        package = self.get_packages(destination)
        if package:
            report = {
                'Destination': package.destination,
                'Hotel': package.hotel,
                'Flights': package.flights,
                'Activities': package.activities,
                'Departure_Time': package.departure,
                'Price': package.price
            }
            return report
        return None

    def calculate_price(self, package):
        prices = {
            'New York': 1000,
            'Paris': 1200,
            'London': 800,
            'Rome': 900,
            'Montreal': 800,
            'Tokyo': 1000,
            'Toronto': 1100,
            'Vancouver': 1200,

            'Hilton': 200,
            'Holiday': 100,
            'Marriott': 300,

            'Air Canada': 500,
            'West Jet': 400,
            'Poter': 300,
            'Air Transit': 200,

            'guided tour': 100,
            'food': 50,
            'excursions': 200,
        }

        destination_price = prices.get(package.destination, 0)
        hotel_price = prices.get(package.hotel, 0)
        flights_price = prices.get(package.flights, 0)
        activities_price = prices.get(package.activities, 0)
        total_price = destination_price + hotel_price + flights_price + activities_price

        return total_price

    def create_table(self):
        connection = sqlite3.connect('database/packages.db')
        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS packages (
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

        message_connection = sqlite3.connect('database/messages.db')
        message_cursor = message_connection.cursor()
        message_cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT,
                    recipient TEXT,
                    content TEXT,
                    timestamp TEXT
                )
            ''')
        message_connection.commit()
        message_cursor.close()
        message_connection.close()

    def store_package(self, package):
        connection = sqlite3.connect('database/packages.db')
        cursor = connection.cursor()
        cursor.execute('''
            INSERT INTO packages (destination, hotel, flights, activities, departure, price)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
        package.destination, package.hotel, package.flights, package.activities, package.departure, package.price))
        connection.commit()
        cursor.close()
        connection.close()

    def show_database(self):
        connection = sqlite3.connect('database/packages.db')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM packages')
        rows = cursor.fetchall()
        cursor.close()
        connection.close()

        packages = []
        for row in rows:
            destination = row[1]
            hotel = row[2]
            flights = row[3]
            activities = row[4]
            departure = row[5]
            price = row[6]
            package = Package(destination, hotel, flights, activities, departure, price)
            packages.append(package)

        return packages

    def check_booking(self):
        customers = self.get_customers_info()
        bookings = []

        for customer in customers:
            customer_bookings = customer.get_book_information().get_bookings()
            bookings.extend(customer_bookings)

        return bookings

    def get_customers_info(self):
        connection = sqlite3.connect('database/accounts.db')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM accounts')
        rows = cursor.fetchall()
        cursor.close()
        connection.close()

        customers = []
        for row in rows:
            username = row[1]
            customer = Customer()
            customer.username = username
            customers.append(customer)

        return customers

    def modify_booking(self, username, booking_id, destination, hotel, flights, activities, departure):
        customer = Customer()
        customer.username = username
        database_folder = "database"
        customer.db_name = f"{database_folder}/{username}_bookings.db"
        book_manager = customer.get_book_information()
        bookings = book_manager.get_bookings()

        for booking in bookings:
            if booking.id == int(booking_id):
                booking.destination = destination
                booking.hotel = hotel
                booking.flights = flights
                booking.activities = activities
                booking.departure = departure

                # book_manager = BookManager(username)
                # book_manager.create_table()
                book_manager.store_booking(booking)  # Update the booking in the customer's database

                return True

        return False

    def receive_message(self, message):
        connection = sqlite3.connect('database/messages.db')
        cursor = connection.cursor()
        cursor.execute('INSERT INTO messages (sender, recipient, content, timestamp) VALUES (?, ?, ?, ?)',
                       (message.sender, message.recipient, message.content, message.timestamp))
        connection.commit()
        cursor.close()
        connection.close()

    # def send_message(self, sender, recipient, content):
    #     message = Message(sender, recipient, content)
    #     self.receive_message(message)
    #     self.store_message(message)

    def send_message(self, recipient, content):
        message = Message(self.username, recipient, content)
        customer = Customer()
        customer.username = self.username
        customer.send_message(recipient, content)
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

    # def calculate_total_revenue(self, username):
    #     total_revenue = 0
    #
    #     book_manager = BookManager(username)
    #     bookings = book_manager.get_bookings()
    #
    #     for booking in bookings:
    #         total_revenue += booking.price
    #
    #     return total_revenue

    def calculate_total_revenue(self):
        total_revenue = 0

        db_files = glob.glob('database/*_bookings.db')  # Get a list of all .db files in the current directory

        for db_file in db_files:
            username = db_file.split('_')[0]  # Extract the username from the file name
            book_manager = BookManager(username)
            bookings = book_manager.get_bookings()

            for booking in bookings:
                total_revenue += booking.price

        return total_revenue

    def generate_bookings_report(self, username):
        report = {}

        book_manager = BookManager(username)
        bookings = book_manager.get_bookings()

        for booking in bookings:
            if booking.destination in report:
                report[booking.destination]['quantity'] += 1
                report[booking.destination]['total_price'] += booking.price
            else:
                report[booking.destination] = {
                    'quantity': 1,
                    'total_price': booking.price
                }

        return report