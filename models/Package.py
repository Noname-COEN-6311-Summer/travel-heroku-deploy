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