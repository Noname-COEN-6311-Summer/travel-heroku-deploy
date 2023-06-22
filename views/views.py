import glob
import sqlite3
import os
from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from datetime import datetime
import stripe
import json
from models import Customer, Agent, Package, Message
from controllers import BookManager, AccountMaanger
account_manager = AccountManager()

app = Flask(__name__)
app.secret_key = os.urandom(24)
stripe.api_key = 'sk_test_51NKDyyBhv3RRjKlwPulSQ7QH4cAcqm8EWVbFLQ45lBLrUrrrGciSgO8ob3rUUKInhtCD51NWGUSoN4aZlxWTPZv000IAjZeXq0'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        search_query = request.form.get('search')
        customer = Customer()
        destination_url = customer.search_destination(search_query)
        if destination_url:
            return redirect(destination_url)
        else:
            return render_template('index.html', search_error=True)

    logged_in = False
    username = None
    if 'logged_in' in session:
        logged_in = session['logged_in']
        username = session.get('username')

    return render_template('index.html', search_error=False, logged_in=logged_in, username=username)


@app.route('/creation', methods=['GET', 'POST'])
def creation():
    agent = Agent()
    book_manager = BookManager(session['username'])

    if request.method == 'POST':
        modification_mode = request.form.get('modification_mode')
        if modification_mode:
            destination = request.form.get('destination')
            hotel = request.form.get('hotel')
            flights = request.form.get('flights')
            activities = request.form.get('activities')
            departure = request.form.get('departure')
            customer = Customer()
            customer.modify_package(destination, hotel, flights, activities, departure)
            return redirect(url_for('creation'))
        else:
            destination = request.form.get('destination')
            hotel = request.form.get('hotel')
            flights = request.form.get('flights')
            activities = request.form.get('activities')
            departure = request.form.get('departure')

            package = Package(destination, hotel, flights, activities, departure, price=0)
            agent.store_package(package)  # Store the new package in the database
            book_manager.store_booking(package)  # Store the new package in the bookings database

            session['package'] = {
                'destination': destination,
                'hotel': hotel,
                'flights': flights,
                'activities': activities,
                'departure': departure,
                'price': agent.calculate_price(package)
            }

            report = agent.represent_packages(package.destination)  # Retrieve the package details for the report

            return render_template('creation.html', package=package, total_price=agent.calculate_price(package), report=report)

    return render_template('creation.html', package=None, total_price=0, report=None)


@app.route('/iceland.html')
def iceland():
    agent = Agent()
    report = agent.represent_packages('iceland')

    session['package'] = {
        'destination': report['Destination'],
        'hotel': report['Hotel'],
        'flights': report['Flights'],
        'activities': report['Activities'],
        'departure': report['Departure_Time'],
        'price': report['Price']
    }

    return render_template('iceland.html', report=report)


@app.route('/greece.html')
def greece():
    agent = Agent()
    report = agent.represent_packages('greece')

    session['package'] = {
        'destination': report['Destination'],
        'hotel': report['Hotel'],
        'flights': report['Flights'],
        'activities': report['Activities'],
        'departure': report['Departure_Time'],
        'price': report['Price']
    }

    return render_template('greece.html', report=report)


@app.route('/banff.html')
def banff():
    agent = Agent()
    report = agent.represent_packages('banff')

    session['package'] = {
        'destination': report['Destination'],
        'hotel': report['Hotel'],
        'flights': report['Flights'],
        'activities': report['Activities'],
        'departure': report['Departure_Time'],
        'price': report['Price']
    }

    return render_template('banff.html', report=report)


@app.route('/<destination>.html')
def destination_page(destination):
    agent = Agent()
    report = agent.represent_packages(destination)
    if report:
        return render_template('destination.html', report=report)
    else:
        return redirect(url_for('index'))

@app.route('/database')
def view_database():
    agent = Agent()
    packages = agent.show_database()
    return render_template('database.html', packages=packages)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error_message = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        favorite_color = request.form['security_answer']

        account_manager.register(username, password, favorite_color)
        return redirect(url_for('index'))

    return render_template('register.html', error_message=error_message)


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_status = None  # Variable to indicate the login status
    error_message = None  # Variable to store the error message

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if account_manager.login(username, password):
            session['logged_in'] = True
            session['username'] = username
            # Store user type (customer or agent) in session
            if username in ['DiWang', 'Melika']:
                session['user_type'] = 'agent'
            else:
                session['user_type'] = 'customer'
            return redirect(url_for('index'))
        else:
            login_status = 'error'
            error_message = 'Invalid username or password.'

    return render_template('login.html', login_status=login_status, error_message=error_message)


@app.route('/logout')
def logout():
    account_manager.logout()
    # Perform logout operations here
    # Redirect to the desired page after logout
    return redirect(url_for('index'))

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    error_message = None
    if request.method == 'POST':
        username = request.form['username']
        security_answer = request.form['security_answer']
        new_password = request.form['new_password']

        account = account_manager.account_security(username)
        if account and account_manager.check_security_answer(username, security_answer):
            account_manager.reset_password(username, new_password)
            return redirect(url_for('login', login_status='success', error_message='Password reset successful. Please log in with your new password.'))
        else:
            error_message = 'Invalid username or security answer.'

    return render_template('reset_password.html', error_message=error_message)


@app.route('/profile')
def profile():
    if 'logged_in' in session and session['logged_in']:
        customer = Customer()
        customer.username = session['username']
        profile = customer.get_profile()
        book_manager = BookManager(session['username'])
        bookings = book_manager.get_bookings()
        # bookings = customer.get_bookings()

        # Fetch the package information from the session
        package_data = session.get('package')
        total_price = request.args.get('total_price')

        for booking in bookings:
            booking.price = customer.agent.calculate_price(booking)

        if package_data:
            package = Package(
                package_data['destination'],
                package_data['hotel'],
                package_data['flights'],
                package_data['activities'],
                package_data['departure'],
                package_data['price']
            )
            bookings.append(package)

        return render_template('profile.html', profile=profile, bookings=bookings, total_price=total_price, book_manager=book_manager)
    else:
        return redirect(url_for('login'))


@app.route('/book', methods=['POST'])
def book():

    if request.method == 'POST':
        # Retrieve the package details from the session
        destination = request.form.get('destination')

        # Get the package details based on the destination
        agent = Agent()
        package = agent.get_packages(destination)

        if package:
            # Store the booking in the database
            customer = Customer()
            customer.username = session['username']
            if customer.book_package(destination):
                customer.agent.store_package(package)
                book_manager = customer.get_book_information()
                book_manager.store_booking(package)

                # Pass the total price as a query parameter to the profile route
                return redirect(url_for('profile', total_price=package.price))
            else:
                return render_template('creation.html')

        return render_template('creation.html')

@app.route('/cancel-booking', methods=['POST'])
def cancel_booking():
    if request.method == 'POST':
        booking_id = request.form.get('booking_id')
        customer = Customer()
        customer.username = session['username']
        customer.cancel_booking(booking_id)
        return redirect(url_for('profile'))

@app.route('/workstation', methods=['GET', 'POST'])
def workstation():
    if 'logged_in' in session and session['logged_in']:
        if session['username'] == 'DiWang' or session['username'] == 'Melika':
            if request.method == 'POST':
                # Handle the form submission
                recipient = request.form.get('recipient')
                content = request.form.get('content')
                agent = Agent()
                agent.username = session['username']
                agent.send_message(recipient, content)
                return redirect(url_for('workstation'))

            agent = Agent()
            customers = agent.get_customers_info()
            bookings = agent.check_booking()
            messages = agent.get_messages(session['username'])
            filtered_customers = [customer for customer in customers if customer.username not in ['DiWang', 'Melika']]
            report = agent.generate_bookings_report(session['username'])
            total_revenue = agent.calculate_total_revenue()


            return render_template('workstation.html', customers=filtered_customers, bookings=bookings, messages=messages, report=report, total_revenue=total_revenue)
        else:
            return "Sorry, you are not an agent."
    else:
        return redirect(url_for('login'))

@app.route('/modify-booking', methods=['POST'])
def modify_booking():
    if request.method == 'POST':
        booking_id = request.form.get('booking_id')
        destination = request.form.get('destination')
        hotel = request.form.get('hotel')
        flights = request.form.get('flights')
        activities = request.form.get('activities')
        departure = request.form.get('departure')

        agent = Agent()
        username = session['username']
        result = agent.modify_booking(username, booking_id, destination, hotel, flights, activities, departure)

        if result:
            return redirect(url_for('workstation'))
        else:
            return redirect(url_for('workstation'))

@app.route('/message', methods=['GET', 'POST'])
def message():
    if 'logged_in' in session and session['logged_in']:
        if session['user_type'] == 'customer':
            if request.method == 'POST':
                recipient = request.form.get('recipient')
                content = request.form.get('content')
                customer = Customer()
                customer.username = session['username']
                customer.send_message(recipient, content)
                return redirect(url_for('message'))

            customer = Customer()
            messages = customer.get_messages(session['username'])
            return render_template('message.html', messages=messages)

        elif session['user_type'] == 'agent':
            if request.method == 'POST':
                recipient = request.form.get('recipient')
                content = request.form.get('content')
                agent = Agent()
                agent.send_message(session['username'], recipient, content)
                return redirect(url_for('workstation'))

            agent = Agent()
            messages = agent.get_messages(session['username'])
            return render_template('message.html', messages=messages)

    else:
        return redirect(url_for('login'))

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'logged_in' in session and session['logged_in']:
        customer = Customer()
        customer.username = session['username']
        book_manager = BookManager(customer.username)
        bookings = book_manager.get_bookings()

        if request.method == 'POST':
            selected_booking = None

            # Get the selected booking from the list of bookings
            for booking in bookings:
                if (
                    booking.destination == request.form.get('destination') and
                    booking.hotel == request.form.get('hotel') and
                    booking.flights == request.form.get('flights') and
                    booking.activities == request.form.get('activities') and
                    booking.departure == request.form.get('departure')
                ):
                    selected_booking = booking
                    break

            if selected_booking:
                amount = max(selected_booking.price, 1)
                # Generate a client secret for the payment intent
                payment_intent = stripe.PaymentIntent.create(
                    amount=amount * 100,  # Stripe expects the amount in cents
                    currency='usd',  # Replace with your preferred currency
                    payment_method_types=['card']
                )

                return render_template('payment.html', booking=selected_booking, stripe_public_key=stripe.api_key,
                                       payment_intent=payment_intent)
            else:
                # Handle the case when the selected booking is not found
                return redirect(url_for('profile'))

        return render_template('payment.html', bookings=bookings)

    return redirect(url_for('login'))

@app.route('/handle-payment', methods=['POST'])
def handle_payment():
    # Retrieve the logged-in user's username
    username = session['username']

    # Retrieve the necessary form data
    destination = request.form.get('destination')
    hotel = request.form.get('hotel')
    flights = request.form.get('flights')
    activities = request.form.get('activities')
    departure = request.form.get('departure')
    price = request.form.get('price')

    # Retrieve the user's bookings from the database
    customer = Customer()
    customer.username = username
    book_manager = BookManager(customer.username)
    bookings = book_manager.get_bookings()

    # Find the matching booking based on the provided booking information
    selected_booking = None
    for booking in bookings:
        if (
            booking.destination == destination
            and booking.hotel == hotel
            and booking.flights == flights
            and booking.activities == activities
            and booking.departure == departure
            and booking.price == price
        ):
            selected_booking = booking
            break

    if selected_booking:
        # Process the payment using the Stripe API

        # If the payment is successful, set the payment_confirmation flag to True
        payment_confirmation = True

        return render_template('payment.html', booking=selected_booking, payment_confirmation=payment_confirmation)

    # If the selected booking is not found, handle the error or redirect to an appropriate page
    return 'Booking not found'




@app.route('/payment-success')
def payment_success():
    return render_template('payment_success.html')

@app.route('/packagelist')
def packagelist():
    return render_template('packagelist.html')
