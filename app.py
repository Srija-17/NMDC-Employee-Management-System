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

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    cursor = conn.cursor()

    query = """
        SELECT 
            e.emp_id AS 'Employee ID',
            e.emp_name AS 'Employee Name',
            t.training_id AS 'Training ID',
            t.training_name AS 'Training Name',
            CASE v.verification_status
                WHEN 0 THEN 'Pending'
                WHEN 1 THEN 'Verified'
                ELSE 'Unknown'
            END AS 'Verification Status'
        FROM verification_status v
        JOIN employee e ON v.emp_id = e.emp_id
        JOIN training t ON v.training_id = t.training_id
        WHERE 1=1
    """

    # --- Added: handle filter from search box ---
    filter_type = request.args.get('filter_type')
    search_value = request.args.get('search_value')

    if filter_type and search_value:
        allowed_filters = {
            "emp_id": "e.emp_id",
            "emp_name": "e.emp_name",
            "training_id": "t.training_id",
            "training_name": "t.training_name",
            "sap_id": "e.sap_id"
        }

        if filter_type in allowed_filters:
            query += f" AND {allowed_filters[filter_type]} LIKE %s"
            cursor.execute(query, (f"%{search_value}%",))
        else:
            cursor.execute(query)
    else:
        cursor.execute(query)

    query += " ORDER BY e.emp_name ASC"

    results = cursor.fetchall()
    cursor.close()

    return render_template(
        'admin_dashboard.html',
        results=results,
        user=session.get('username')
    )


@app.route('/manage_employee')
def manage_employee():
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT e.emp_id, e.emp_name, e.sap_id, e.designation, d.dept_name
            FROM employee e
            LEFT JOIN department d ON e.dept_id = d.dept_id
        """)
        employees = cursor.fetchall()
    return render_template('manage_employee.html', employees=employees)

@app.route('/manage_training', methods=['GET'])
def manage_training():
    cursor = conn.cursor()

    query = """
        SELECT 
            e.emp_id AS 'Employee ID',
            e.sap_id AS 'SAP ID',
            e.emp_name AS 'Employee Name',
            t.training_id AS 'Training ID',
            t.training_name AS 'Training Name',
            tr.scheduled_date AS 'Scheduled Date',
            tr.joining_date AS 'Joining Date',
            tr.completion_date AS 'Completion Date',
            tr.status AS 'Status'
        FROM trainee tr
        JOIN employee e ON tr.emp_id = e.emp_id
        JOIN training t ON tr.training_id = t.training_id
        WHERE 1=1
    """

    filter_type = request.args.get('filter_type')
    search_value = request.args.get('search_value')

    if filter_type and search_value:
        if filter_type in ["emp_name", "emp_id", "sap_id", "training_name", "training_id"]:
            table_alias = 'e.' if filter_type.startswith('emp') or filter_type == 'sap_id' else 't.'
            query += f" AND {table_alias}{filter_type} LIKE %s"
            search_value = f"%{search_value}%"

    query += " ORDER BY e.emp_name ASC"

    if filter_type and search_value:
        cursor.execute(query, (search_value,))
    else:
        cursor.execute(query)

    results = cursor.fetchall()
    cursor.close()

    return render_template(
        'admin_dashboard.html',
        results=results,
        user=session.get('username')
    )
@app.route('/update_training_bulk', methods=['POST'])
def update_training_bulk():
    data = request.json
    cursor = conn.cursor()

    try:
        for row in data:
            sql = """
                UPDATE trainee
                SET scheduled_date = %s,
                    joining_date = %s,
                    completion_date = %s,
                    status = %s
                WHERE emp_id = %s AND training_id = %s
            """
            cursor.execute(sql, (
                row.get('scheduled_date') or None,
                row.get('joining_date') or None,
                row.get('completion_date') or None,
                row.get('status'),  # active/inactive
                row['emp_id'],
                row['training_id']
            ))

        conn.commit()
        return {"success": True, "message": "Training records updated successfully"}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}, 500
@app.route('/manage_user', methods=['GET'])
def manage_user():
    cursor = conn.cursor()

    query = """
        SELECT user_id AS 'User ID',
               username AS 'Username',
               password AS 'Password',
               role AS 'Role'
        FROM `user`
        WHERE 1=1
    """

    filter_type = request.args.get('filter_type')
    search_value = request.args.get('search_value')

    if filter_type and search_value:
        if filter_type == "username":
            query += " AND username LIKE %s"
            search_value = f"%{search_value}%"
        elif filter_type == "role":
            query += " AND role = %s"  # exact match for role

    query += " ORDER BY username ASC"

    if filter_type and search_value:
        cursor.execute(query, (search_value,))
    else:
        cursor.execute(query)

    users = cursor.fetchall()
    cursor.close()

    return render_template(
        'manage_user.html',
        users=users,
        user=session.get('username')
    )

@app.route('/update_users_bulk', methods=['POST'])
def update_users_bulk():
    data = request.json
    cursor = conn.cursor()

    try:
        for row in data:
            sql = """
                UPDATE user
                SET username = %s,
                    password = %s,
                    role = %s
                WHERE user_id = %s
            """
            cursor.execute(sql, (
                row.get('username'),
                row.get('password'),
                row.get('role'),
                row['user_id']
            ))

        conn.commit()
        return {"success": True, "message": "Users updated successfully"}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}, 500

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

    params = []

    if request.method == 'POST':
        filter_type = request.form.get('filter_type')
        search_value = request.form.get('search_value')

        if filter_type == 'emp_name':
            base_query += " AND e.emp_name LIKE %s"
            params.append(f"%{search_value}%")
        elif filter_type == 'emp_id':
            base_query += " AND e.emp_id = %s"
            params.append(search_value)
        elif filter_type == 'sap_id':
            base_query += " AND e.sap_id = %s"
            params.append(search_value)
        elif filter_type == 'department':
            dept_value = request.form.get('department') or search_value
            if dept_value:
                base_query += " AND d.dept_name = %s"
                params.append(dept_value)
        elif filter_type == 'training_name':
            base_query += " AND tr.training_name LIKE %s"
            params.append(f"%{search_value}%")
        elif filter_type == 'training_date':
            join_date = request.form.get('joining_date')
            comp_date = request.form.get('completion_date')
            if join_date and comp_date:
                base_query += " AND tn.joining_date <= %s AND tn.completion_date >= %s"
                params.extend([comp_date, join_date])
        elif filter_type == 'due':
            base_query += """
                AND DATE_ADD(tn.completion_date, INTERVAL tr.period YEAR)
                BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
            """

    base_query += " ORDER BY e.emp_name ASC"

    cursor.execute(base_query, tuple(params))
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

@app.route('/add_trainee', methods=['GET', 'POST'])
def add_trainee():
    cursor = conn.cursor()
    cursor.execute("SELECT emp_id, emp_name FROM employee")
    employees = cursor.fetchall()

    cursor.execute("SELECT training_id, training_name FROM training")
    trainings = cursor.fetchall()

    error_message = None
    success_message = None

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

            # Set success message instead of redirect
            success_message = "Trainee added successfully."

        except pymysql.err.IntegrityError as e:
            if e.args[0] == 1452:  # Foreign key constraint fails
                error_message = "The employee or training does not exist."
            else:
                error_message = str(e)

    return render_template('add_trainee.html',
                           employees=employees,
                           trainings=trainings,
                           error_message=error_message,
                           success_message=success_message)

@app.route('/check_employee/<emp_id>')
def check_employee(emp_id):
    cursor = conn.cursor()
    cursor.execute("SELECT emp_id FROM employee WHERE emp_id = %s", (emp_id,))
    result = cursor.fetchone()
    return {"exists": bool(result)}

@app.route('/reviewer2')
def reviewer2():
    return render_template('reviewer2_dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)