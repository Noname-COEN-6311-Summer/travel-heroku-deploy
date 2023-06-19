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


class Package:
    def __init__(self, destination, hotel, flights, activities, departure, price):
        self.destination = destination
        self.hotel = hotel
        self.flights = flights
        self.activities = activities
        self.departure = departure
        self.price = price

    def represent_packages(destination):
        agent = Agent()
        package = agent.get_packages(destination)
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
        connection = sqlite3.connect('packages.db')
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

        message_connection = sqlite3.connect('messages.db')
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
        connection = sqlite3.connect('packages.db')
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
        connection = sqlite3.connect('packages.db')
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
        connection = sqlite3.connect('accounts.db')
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
        customer.db_name = f'{username}_bookings.db'
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
        connection = sqlite3.connect('messages.db')
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
        connection = sqlite3.connect('messages.db')
        cursor = connection.cursor()
        cursor.execute('INSERT INTO messages (sender, recipient, content, timestamp) VALUES (?, ?, ?, ?)',
                       (message.sender, message.recipient, message.content, message.timestamp))
        connection.commit()
        cursor.close()
        connection.close()

    def get_messages(self, username):
        connection = sqlite3.connect('messages.db')
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

        db_files = glob.glob('*_bookings.db')  # Get a list of all .db files in the current directory

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


class Customer:
    def __init__(self):
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
        self.username = username  # Store the logged-in username
        self.db_name = f'{self.username}_bookings.db'

    def get_profile(self):
        if self.username:
            username = self.username  # Store the username in a local variable
            # Fetch the user profile details from the database based on the stored username
            connection = sqlite3.connect('accounts.db')
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
        connection = sqlite3.connect('bookings.db')
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

        db_name = f'{self.username}_bookings.db'

        connection = sqlite3.connect(db_name)
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
        connection = sqlite3.connect('messages.db')
        cursor = connection.cursor()
        cursor.execute('INSERT INTO messages (sender, recipient, content, timestamp) VALUES (?, ?, ?, ?)',
                       (message.sender, message.recipient, message.content, message.timestamp))
        connection.commit()
        cursor.close()
        connection.close()

    def get_messages(self, username):
        connection = sqlite3.connect('messages.db')
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

class Message:
    def __init__(self, sender, recipient, content):
        self.sender = sender
        self.recipient = recipient
        self.content = content
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# book_manager = BookManager()