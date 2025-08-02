from flask import Flask, render_template,url_for, session, request, redirect, session, send_file, jsonify, flash
import pymysql 
import csv
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL connection
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='nmdc',
    cursorclass=pymysql.cursors.DictCursor
)

# ✅ Redirect root to login
@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = False
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = conn.cursor()  # ✅ FIXED: Define cursor
        query = "SELECT * FROM user WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = user['username']
            session['role'] = user['role']

            # Redirect based on role
            if user['role'] == 'admin':
                return redirect('/admin')
            elif user['role'] == 'reviewer_one':
                return redirect('/reviewer_one')
            elif user['role'] == 'reviewer_two':
                return redirect('/reviewer2')
        else:
            error = True
            flash('Invalid username or password.')

    return render_template('login.html', error=error)
@app.route('/logout')
def logout():
    session.clear()  # Clears the session (logs out the user)
    return redirect(url_for('login'))

@app.route('/admin')
def admin_dashboard():
    cursor = conn.cursor()

    # Fetch verification report with employee & training details
    cursor.execute("""
        SELECT 
            e.emp_name,
            e.emp_id,
            t.training_name,
            t.training_id,
            vs.verification_status
        FROM verification_status vs
        JOIN employee e ON vs.emp_id = e.emp_id
        JOIN training t ON vs.training_id = t.training_id
    """)

    report_data = cursor.fetchall()

    return render_template('admin_dashboard.html', report_data=report_data)

@app.route('/manage_employee')
def manage_employee():
    return "<h1>Manage Employee Page</h1>"

@app.route('/manage_training')
def manage_training():
    return "<h1>Manage Training Page</h1>"

@app.route('/download_data')
def download_data():
    return "<h1>Download Page</h1>"

@app.route('/reviewer_one', methods=['GET', 'POST'])
def reviewer_one():
    cursor = conn.cursor()

    # Get logged-in reviewer username
    cursor.execute("SELECT username FROM user WHERE role='reviewer_one'")
    user_data = cursor.fetchone()

    # Get department names for dropdown
    cursor.execute("SELECT dept_name FROM department")
    departments = [row['dept_name'] for row in cursor.fetchall()]

    search_results = []

    # Base query with proper joins
    base_query = """
        SELECT 
            e.emp_id,
            e.emp_name,
            e.sap_id,
            d.dept_name,
            e.designation,
            tr.training_name,
            tr.period,
            tn.scheduled_date,
            tn.joining_date,
            tn.completion_date
        FROM trainee tn
        JOIN employee e ON tn.emp_id = e.emp_id
        JOIN training tr ON tn.training_id = tr.training_id
        LEFT JOIN department d ON e.dept_id = d.dept_id
        WHERE 1=1
    """

    if request.method == 'POST':
        filters = []

        filter_type = request.form.get('filter_type')
        search_value = request.form.get('search_value')

        if filter_type == 'emp_name':
            filters.append(f"AND e.emp_name LIKE '%{search_value}%'")
        elif filter_type == 'emp_id':
            filters.append(f"AND e.emp_id = '{search_value}'")
        elif filter_type == 'sap_id':
            filters.append(f"AND e.sap_id = '{search_value}'")
        elif filter_type == 'department':
            filters.append(f"AND d.dept_name = '{search_value}'")
        elif filter_type == 'training_name':
            filters.append(f"AND tr.training_name LIKE '%{search_value}%'")
        elif filter_type == 'training_date':
            join_date = request.form.get('joining_date')
            comp_date = request.form.get('completion_date')
            if join_date and comp_date:
                filters.append(f"""
                    AND tn.joining_date <= '{comp_date}'
                    AND tn.completion_date >= '{join_date}'
                """)

        elif filter_type == 'due':
            filters.append("""
                AND DATE_ADD(tn.completion_date, INTERVAL tr.period YEAR)
                BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
            """)

        # Combine query
        final_query = base_query + " " + " ".join(filters)

        # Debug print (optional)
        print("Executing SQL:", final_query)

        cursor.execute(final_query)
        search_results = cursor.fetchall()

    return render_template(
        'reviewer1_dashboard.html',
        user=user_data['username'],
        departments=departments,
        results=search_results
    )

@app.route('/download', methods=['POST'])
def download():
    results = request.json.get('results', [])
    if not results:
        return "No data", 400

    si = io.StringIO()
    writer = csv.DictWriter(si, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)

    return send_file(output, mimetype='text/csv', as_attachment=True, download_name='results.csv')

from flask import Flask, render_template, request, redirect, url_for, flash
import pymysql

@app.route('/add_trainee', methods=['GET', 'POST'])
def add_trainee():
    cursor = conn.cursor()
    cursor.execute("SELECT emp_id, emp_name FROM employee")
    employees = cursor.fetchall()

    cursor.execute("SELECT training_id, training_name FROM training")
    trainings = cursor.fetchall()

    error_message = None

    if request.method == 'POST':
        emp_id = request.form.get('emp_id')
        training_id = request.form.get('training_id')
        scheduled_date = request.form.get('scheduled_date') or None
        joining_date = request.form.get('joining_date') or None
        completion_date = request.form.get('completion_date') or None

        try:
            sql = """
                INSERT INTO trainee (emp_id, training_id, scheduled_date, joining_date, completion_date)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (emp_id, training_id, scheduled_date, joining_date, completion_date))
            conn.commit()
            return redirect(url_for('reviewer_one'))

        except pymysql.err.IntegrityError as e:
            # MySQL error 1452 = foreign key constraint fails
            if e.args[0] == 1452:
                error_message = "The employee does not exist"
            else:
                error_message = str(e)

    return render_template('add_trainee.html',
                           employees=employees,
                           trainings=trainings,
                           error_message=error_message)


@app.route('/check_employee/<emp_id>')
def check_employee(emp_id):
    cursor = conn.cursor()
    cursor.execute("SELECT emp_id FROM employee WHERE emp_id = %s", (emp_id,))
    result = cursor.fetchone()
    return {"exists": bool(result)}

@app.route('/check_training/<training_id>')
def check_training(training_id):
    cursor = conn.cursor()
    cursor.execute("SELECT training_id FROM training WHERE training_id = %s", (training_id,))
    result = cursor.fetchone()
    return {"exists": bool(result)}

@app.route('/reviewer2')
def reviewer2():
    return render_template('reviewer2_dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)