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

class Message:
    def __init__(self, sender, recipient, content):
        self.sender = sender
        self.recipient = recipient
        self.content = content
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

