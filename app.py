from flask import Flask, render_template,url_for, session, request, redirect, session, send_file, jsonify, flash
import pymysql 
import csv
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Global status map for all templates
app.jinja_env.globals['status_map'] = {
    0: "Not Verified",
    1: "Verified",
    2: "Verified by R2",
    -1: "Rejected by R1",
    -2: "Rejected by R2"
}

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
        if filter_type in ["emp_id", "sap_id"]:
            # Exact match for emp_id and sap_id
            query += f" AND e.{filter_type} = %s"
        elif filter_type in ["emp_name", "training_name", "training_id"]:
            # Partial match for others
            if filter_type.startswith('emp'):
                table_alias = 'e.'
            else:
                table_alias = 't.'
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
    
@app.route('/manage_user', methods=['GET', 'POST'])
def manage_user():
    cursor = conn.cursor(pymysql.cursors.DictCursor)  # ✅ Correct for PyMySQL

    cursor.execute("SELECT DISTINCT role FROM user")
    roles = [row['role'] for row in cursor.fetchall()]

    search_results = []

    base_query = """
        SELECT user_id AS 'User ID',
               username AS 'Username',
               password AS 'Password',
               role AS 'Role'
        FROM `user`
        WHERE 1=1
    """
    params = []

    filter_type = request.values.get('filter_type')
    search_value = request.values.get('search_value')
    role_value = request.values.get('role')

    if filter_type == 'username' and search_value:
        base_query += " AND username LIKE %s"
        params.append(f"%{search_value}%")
    elif filter_type == 'role' and role_value:
        base_query += " AND role = %s"
        params.append(role_value)

    cursor.execute(base_query, tuple(params))
    search_results = cursor.fetchall()
    cursor.close()

    return render_template(
        'manage_user.html',
        user=session.get('username'),
        roles=roles,
        users=search_results
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
        return jsonify(success=True, message="Users updated successfully")
    except Exception as e:
        conn.rollback()
        return jsonify(success=False, message=str(e)), 500
    
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
    cursor.close()
    return {"exists": bool(result)}

@app.route('/verification', methods=['GET'])
def verification():
    verification_filter = request.args.get('filter', 'all')

    cursor = conn.cursor(pymysql.cursors.DictCursor)

    base_query = """
        SELECT e.emp_id, e.emp_name, e.designation, d.dept_name,
               t.training_id, t.training_name,
               tr.scheduled_date, tr.joining_date, tr.completion_date,
               tr.verification
        FROM employee e
        JOIN department d ON e.dept_id = d.dept_id
        JOIN trainee tr ON e.emp_id = tr.emp_id
        JOIN training t ON tr.training_id = t.training_id
    """

    if verification_filter == 'verified':
        base_query += " WHERE tr.verification = 1"
    elif verification_filter == 'not_verified':
        base_query += " WHERE tr.verification = 0"
    elif verification_filter == 'rejected':
        base_query += " WHERE tr.verification = -1"
    else:  # default 'all'
        base_query += " WHERE tr.verification IN (0, 1, -1)"

    cursor.execute(base_query)
    data = cursor.fetchall()

    status_map = {
        0: "Not Verified",
        1: "Verified",
        -1: "Rejected"
    }

    return render_template(
        'verification.html',
        data=data,
        status_map=status_map,
        current_filter=verification_filter
    )

@app.route('/verification/update', methods=['POST'])
def verification_update():
    certificate_id = request.form.get('certificate_id')
    new_status = int(request.form.get('new_status'))

    cursor = conn.cursor()
    cursor.execute("""
        UPDATE verification_status
        SET verification_status = %s
        WHERE certificate_id = %s
    """, (new_status, certificate_id))
    conn.commit()
    cursor.close()

    return jsonify({
        'success': True,
        'new_status_map': app.jinja_env.globals['status_map'].get(new_status, 'Unknown')
    })


@app.route('/trainee_verification', methods=['GET'])
def trainee_verification():
    # require login
    if 'username' not in session:
        return redirect(url_for('login'))  # adjust to your login route

    cursor = conn.cursor(pymysql.cursors.DictCursor)

    username = session['username']
    cursor.execute("SELECT role FROM user WHERE username = %s", (username,))
    u = cursor.fetchone()
    role = u['role'] if u else 'admin'   # fallback to admin if missing (adjust as needed)

    # Mapping keys used in the dropdown (human labels only in HTML)
    status_map = {
        'not_verified': 0,
        'verified': 1,
        'rejected': -1
    }

    sel_key = request.args.get('status')  # values: 'not_verified', 'verified', 'rejected' or None

    base_query = """
        SELECT
            tn.emp_id,
            e.emp_name,
            tn.training_id,
            tr.training_name,
            tn.scheduled_date,
            tn.joining_date,
            tn.completion_date,
            tn.verification
        FROM trainee tn
        JOIN employee e ON tn.emp_id = e.emp_id
        JOIN training tr ON tn.training_id = tr.training_id
        WHERE 1=1
    """
    params = []

    # Enforce role rules:
    if role == 'reviewer_two':
        # reviewer_two always sees only verified (1)
        base_query += " AND tn.verification = %s"
        params.append(1)
        # ignore any sel_key from UI
        effective_key = 'verified'
    else:
        # reviewer_one and admin:
        if sel_key in status_map:
            base_query += " AND tn.verification = %s"
            params.append(status_map[sel_key])
            effective_key = sel_key
        else:
            # default page view: show only 0, 1, -1
            base_query += " AND tn.verification IN (0, 1, -1)"
            effective_key = ''  # means All (the dropdown will show "All")

    base_query += " ORDER BY tn.emp_id ASC"

    cursor.execute(base_query, tuple(params))
    rows = cursor.fetchall()
    cursor.close()

    return render_template(
        'trainee_verification.html',
        data=rows,
        role=role,
        selected_key=effective_key  # used to mark dropdown
    )
@app.route('/verification/update_bulk', methods=['POST'])
def verification_update_bulk():
    updates = request.get_json()
    if not updates:
        return jsonify({"success": False, "error": "No updates received"})

    try:
        cursor = conn.cursor()
        for key, status in updates.items():
            emp_id, training_id = key.split("_")
            cursor.execute("""
                UPDATE trainee
                SET verification = %s
                WHERE emp_id = %s AND training_id = %s
            """, (status, emp_id, training_id))
        conn.commit()
        cursor.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/reviewer2')
def reviewer2():
    return render_template('reviewer2_dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)