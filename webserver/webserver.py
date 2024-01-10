# webserver/webserver.py
import sqlite3
from flask import Flask, render_template, request, session, jsonify, redirect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'the random string'

def get_db_connection():

    # Change the filepath later.
    conn = sqlite3.connect("PycharmProjects/NetStormer/db/data/your_nmap_output")
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
    if 'logged_in' in session and session['logged_in']:
        if request.method == 'POST':
            user_input = request.form.get('user_input')
            try:
                conn = get_db_connection()
                query_result = conn.execute(user_input).fetchall()
                columns = query_result[0].keys() if query_result else []
                conn.close()
                return render_template('index.html', result=query_result, columns=columns)

            except Exception as e:
                return jsonify({'error': str(e)})

        elif request.method == 'GET':
            table_data = get_tables_and_data()
            return render_template('index.html', table_data=table_data)

    else:
        return render_template('login.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == 'password' and request.form['username'] == 'admin':
            session['logged_in'] = True
            return redirect('index.html')
    else:
        return render_template('login.html')

@app.route('/query', methods=['GET', 'POST'])
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
