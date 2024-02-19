from sanitize import InputSanitizer
from bcrypt import checkpw
from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
#from terminal.data import TerminalData
import sqlite3
import os


def find_db_files(directory='.'):
    db_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            # the "Select a project" file is so there is a default option that gets selected.
            if file.endswith('.db') and not file.endswith('projects.db') and not file.endswith('user.db') or file.endswith("Select a Project"):
                db_files.append(os.path.join(root, file))

    return db_files


def get_tables_and_data(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]

    table_data = []

    for table in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        columns = [column[1] for column in cursor.fetchall()]

        cursor.execute(f"SELECT * FROM {table};")
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        table_data.append({"table": table, "columns": columns, "rows": rows})

    conn.close()
    return table_data


class DB:
    def __init__(self, db_files):
        self.db_files = db_files

    def api_get_file_list(self):
        if not self.db_files:
            return jsonify({"error": "No database files found."})

        file_names = [os.path.basename(db_file) for db_file in self.db_files]
        return jsonify(file_names)

    def api_get_table_data(self, project_name):
        if not self.db_files:
            return jsonify({"error": "No database files found."})

        if project_name not in [os.path.basename(db_file) for db_file in self.db_files]:
            return jsonify({"error": "Invalid project name."})

        selected_db_file = [db_file for db_file in self.db_files if project_name == os.path.basename(db_file)][0]

        table_data = get_tables_and_data(selected_db_file)

        return jsonify({'tables': table_data})

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(12)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


db_files = find_db_files()
api_instance = DB(db_files)


class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id


# TODO Change the filepath later.
def authenticate(username, password):
    data_dir = '/home/kali/PycharmProjects/NetStormer/db/data/user.db'
    username = InputSanitizer.sanitize_input(username)
    with sqlite3.connect(data_dir) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        if user_data:
            stored_password = user_data[2].encode('utf-8')
            password = password.encode('utf-8')
            if checkpw(password, stored_password):
                session['role'] = user_data[3]
                return User(1)  # Assuming user_id is at index 0
        return None


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


def get_db_connection():

    # TODO Change the filepath later.
    conn = sqlite3.connect("/home/kali/PycharmProjects/NetStormer/db/data/projects/deez/your_nmap_output.db")

    conn.row_factory = sqlite3.Row
    return conn


@app.route('/api/getFileList')
def api_get_file_list():
    return api_instance.api_get_file_list()


@app.route('/api/getTableData/<project_name>')
def api_get_table_data(project_name):
    return api_instance.api_get_table_data(project_name)


@app.route('/', methods=['GET', 'POST'])
def index():
    if not current_user.is_authenticated:
        return redirect('login', code=302)
    elif session['role'] != 'admin':
        return redirect(url_for('error'))
    else:
        if request.method == 'GET':
            file_names = api_instance.api_get_file_list().json
            return render_template('index.html', file_names=file_names)
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
    if session['role'] != 'admin':
        return redirect(url_for('error'))
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


@app.route('/error', methods=['GET'])
def error():
    return render_template('404.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999, debug=False)
