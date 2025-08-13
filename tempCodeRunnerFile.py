@app.route('/verification', methods=['GET', 'POST'])
def verification():
    if 'username' not in session:
        return redirect(url_for('login'))  # or your login route
    
    cursor = conn.cursor()

    # Get current logged-in user info (assuming username and role stored in session)
    username = session['username']
    role = session.get('role')  # 'reviewer_one', 'reviewer_two', or 'admin'

    # Base query with joins to get verification data with employee/training info
    base_query = """
        SELECT
            vs.certificate_id,
            vs.emp_id,
            e.emp_name,
            vs.training_id,
            tr.training_name,
            vs.verification_status
        FROM verification_status vs
        JOIN employee e ON vs.emp_id = e.emp_id
        JOIN training tr ON vs.training_id = tr.training_id
        WHERE 1=1
    """

    params = []

    # Role-based filtering:
    if role == 'reviewer_one':
        # Show pending (0) and rejected (-1) only
        base_query += " AND vs.verification_status IN (0, -1)"
    elif role == 'reviewer_two':
        # Show only accepted by reviewer_one (1)
        base_query += " AND vs.verification_status = 1"
    elif role == 'admin':
        # Admin sees all, no filter needed
        pass
    else:
        # Unauthorized role
        return "Unauthorized", 403

    base_query += " ORDER BY e.emp_name"

    cursor.execute(base_query, tuple(params))
    data = cursor.fetchall()

    return render_template('verification.html', data=data, role=role)


@app.route('/verification/update', methods=['POST'])
def verification_update():
    certificate_id = request.form.get('certificate_id')
    new_status = int(request.form.get('new_status'))

    status_map = {
        0: "Not Verified",
        1: "Verified",
        -1: "Rejected"
    }

    cursor = conn.cursor()
    cursor.execute("""
        UPDATE verification_status
        SET verification_status = %s
        WHERE certificate_id = %s
    """, (new_status, certificate_id))
    conn.commit()

    return jsonify({
        'success': True,
        'new_status_map': status_map.get(new_status, 'Unknown')
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