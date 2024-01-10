# webserver/webserver.py
import sqlite3
from flask import Flask, render_template, request, session, jsonify, redirect
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
app = Flask(__name__, template_folder="templates")
app.config['SECRET_KEY'] = 'the random string'

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

def authenticate(username, password):
    # Example: Check if username and password match a user in your database
    # If yes, return the user object; otherwise, return None
    if username == 'admin' and password == 'password':
        return User(1)
    return None

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

def get_db_connection():

    # Change the filepath later.
    conn = sqlite3.connect("/home/kyand/NetStormer/db/data/your_nmap_output")
    conn.row_factory = sqlite3.Row
    return conn

def get_tables_and_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]

    table_data = []

    for table in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        columns = [column[1] for column in cursor.fetchall()]

        cursor.execute(f"SELECT * FROM {table};")
        rows = [dict(row) for row in cursor.fetchall()]

        table_data.append((table, columns, rows))

    conn.close()
    return table_data


@app.route('/', methods=['GET', 'POST'])
def index():
    if not current_user.is_authenticated:
        return redirect('login', code=302)
    else:
        if request.method == 'GET':
            table_data = get_tables_and_data()
            return render_template('index.html', table_data=table_data)
        elif request.method == 'POST':
            user_input = request.form.get('user_input')
            try:
                conn = get_db_connection()
                query_result = conn.execute(user_input).fetchall()
                columns = query_result[0].keys() if query_result else []
                conn.close()
                return render_template('index.html', result=query_result, columns=columns)

            except Exception as e:
                return jsonify({'error': str(e)})
# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = authenticate(request.form['username'], request.form['password'])
        if user:
            # Log in the user using Flask-Login
            login_user(user)
            return redirect('/', code=302)
    else:
        return render_template('login.html')
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('login')
@app.route('/query', methods=['GET', 'POST'])
@login_required
def query():
    if request.method == 'POST':
        user_input = request.form.get('user_input')
        try:
            conn = get_db_connection()
            query_result = conn.execute(user_input).fetchall()
            conn.close()
            result_list = [dict(row) for row in query_result]
            return jsonify(result_list)

        except Exception as e:
            return jsonify({'error': str(e)})

    return render_template('query.html')

if __name__ == "__main__":
    app.run(port=9999, debug=False)