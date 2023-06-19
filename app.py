from flask import Flask

app = Flask(__name__, static_url_path='/static')

# Configure the template and static file locations
app.template_folder = 'templates'
app.static_folder = 'static'
app.secret_key = '123'
# Import the routes from views.py
from views.views import index, iceland, greece, banff, destination_page, view_database, register, login, logout, reset_password, profile, book, cancel_booking, workstation, modify_booking, message, payment, handle_payment, payment_success

# Register the routes with the app
app.route('/')(index)
app.route('/iceland.html')(iceland)
app.route('/greece.html')(greece)
app.route('/banff.html')(banff)
app.route('/<destination>.html')(destination_page)
app.route('/database')(view_database)
app.route('/register', methods=['GET', 'POST'])(register)
app.route('/login', methods=['GET', 'POST'])(login)
app.route('/logout')(logout)
app.route('/reset_password', methods=['GET', 'POST'])(reset_password)
app.route('/profile')(profile)
app.route('/book', methods=['POST'])(book)
app.route('/cancel-booking', methods=['POST'])(cancel_booking)
app.route('/workstation', methods=['GET', 'POST'])(workstation)
app.route('/modify-booking', methods=['POST'])(modify_booking)
app.route('/message', methods=['GET', 'POST'])(message)
app.route('/payment', methods=['GET', 'POST'])(payment)
app.route('/handle-payment', methods=['POST'])(handle_payment)
app.route('/payment-success')(payment_success)

if __name__ == '__main__':
    app.run(debug=True)
