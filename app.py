#!/usr/bin/env python
# coding: utf-8

# In[ ]:





# In[ ]:


# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from datetime import datetime
import re

app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'kavya2004'
app.config['MYSQL_DB'] = 'attendance_system'
app.secret_key = 'your_secret_key'

mysql = MySQL(app)

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        student_id = request.form['student_id']
        name = request.form['name']
        email = request.form['email']
        age = request.form['age']
        gender = request.form['gender']
        phone = request.form['phone']
        password = request.form['password']

        # Check if student_id or email already exists
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM students WHERE student_id = %s OR email = %s', (student_id, email))
        account = cursor.fetchone()

        if account:
            flash('Account already exists!')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address!')
        else:
            cursor.execute('INSERT INTO students VALUES (%s, %s, %s, %s, %s, %s, %s)', 
                         (student_id, name, email, age, gender, phone, password))
            mysql.connection.commit()
            flash('Registration successful!')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_type = request.form['user_type']
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        
        if user_type == 'student':
            cursor.execute('SELECT * FROM students WHERE student_id = %s AND password = %s', (username, password))
        else:
            cursor.execute('SELECT * FROM teachers WHERE teacher_id = %s AND password = %s', (username, password))
        
        account = cursor.fetchone()
        
        if account:
            session['logged_in'] = True
            session['user_type'] = user_type
            session['username'] = username
            
            if user_type == 'student':
                return redirect(url_for('student_dashboard'))
            else:
                return redirect(url_for('teacher_dashboard'))
        else:
            flash('Invalid credentials!')
            
    return render_template('login.html')

@app.route('/student_dashboard')
def student_dashboard():
    if 'logged_in' in session and session['user_type'] == 'student':
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM students WHERE student_id = %s', [session['username']])
        student = cursor.fetchone()
        
        cursor.execute('''
            SELECT date, status 
            FROM attendance 
            WHERE student_id = %s 
            ORDER BY date DESC
        ''', [session['username']])
        attendance = cursor.fetchall()
        
        return render_template('student_dashboard.html', student=student, attendance=attendance)
    return redirect(url_for('login'))

@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'logged_in' in session and session['user_type'] == 'teacher':
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM students')
        students = cursor.fetchall()
        return render_template('teacher_dashboard.html', students=students)
    return redirect(url_for('login'))

@app.route('/mark_attendance', methods=['GET', 'POST'])
def mark_attendance():
    if 'logged_in' in session and session['user_type'] == 'teacher':
        if request.method == 'POST':
            date = request.form['date']
            attendance_data = request.form.getlist('attendance[]')
            student_ids = request.form.getlist('student_id[]')
            
            cursor = mysql.connection.cursor()
            
            for student_id, status in zip(student_ids, attendance_data):
                cursor.execute('''
                    INSERT INTO attendance (student_id, date, status)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE status = %s
                ''', (student_id, date, status, status))
                
            mysql.connection.commit()
            flash('Attendance marked successfully!')
            
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM students')
        students = cursor.fetchall()
        return render_template('mark_attendance.html', students=students)
    return redirect(url_for('login'))

@app.route('/search_student', methods=['POST'])
def search_student():
    if 'logged_in' in session and session['user_type'] == 'teacher':
        search_term = request.form['search_term']
        cursor = mysql.connection.cursor()
        cursor.execute('''
            SELECT * FROM students 
            WHERE student_id LIKE %s 
            OR name LIKE %s
        ''', (f'%{search_term}%', f'%{search_term}%'))
        students = cursor.fetchall()
        return render_template('teacher_dashboard.html', students=students)
    return redirect(url_for('login'))

# Add these new routes to your app.py

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'logged_in' in session and session['user_type'] == 'teacher':
        if request.method == 'POST':
            student_id = request.form['student_id']
            name = request.form['name']
            email = request.form['email']
            age = request.form['age']
            gender = request.form['gender']
            phone = request.form['phone']
            password = request.form['password']  # In production, use proper password hashing

            cursor = mysql.connection.cursor()
            
            # Check if student already exists
            cursor.execute('SELECT * FROM students WHERE student_id = %s OR email = %s', (student_id, email))
            if cursor.fetchone():
                flash('Student ID or email already exists!')
            else:
                cursor.execute('INSERT INTO students VALUES (%s, %s, %s, %s, %s, %s, %s)',
                             (student_id, name, email, age, gender, phone, password))
                mysql.connection.commit()
                flash('Student added successfully!')
                return redirect(url_for('teacher_dashboard'))
                
        return render_template('add_student.html')
    return redirect(url_for('login'))

@app.route('/remove_student/<string:student_id>')
def remove_student(student_id):
    if 'logged_in' in session and session['user_type'] == 'teacher':
        cursor = mysql.connection.cursor()
        
        # Remove student's attendance records first (foreign key constraint)
        cursor.execute('DELETE FROM attendance WHERE student_id = %s', [student_id])
        
        # Remove student
        cursor.execute('DELETE FROM students WHERE student_id = %s', [student_id])
        mysql.connection.commit()
        
        flash('Student removed successfully!')
        return redirect(url_for('teacher_dashboard'))
    return redirect(url_for('login'))

@app.route('/edit_student/<string:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    if 'logged_in' in session and session['user_type'] == 'teacher':
        cursor = mysql.connection.cursor()
        
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            age = request.form['age']
            gender = request.form['gender']
            phone = request.form['phone']
            
            # Check if email is already used by another student
            cursor.execute('SELECT * FROM students WHERE email = %s AND student_id != %s', (email, student_id))
            if cursor.fetchone():
                flash('Email already in use by another student!')
            else:
                cursor.execute('''
                    UPDATE students 
                    SET name = %s, email = %s, age = %s, gender = %s, phone = %s 
                    WHERE student_id = %s
                ''', (name, email, age, gender, phone, student_id))
                mysql.connection.commit()
                flash('Student information updated successfully!')
                return redirect(url_for('teacher_dashboard'))
        
        # Get student data for pre-filling the form
        cursor.execute('SELECT * FROM students WHERE student_id = %s', [student_id])
        student = cursor.fetchone()
        if student:
            return render_template('edit_student.html', student=student)
        flash('Student not found!')
        return redirect(url_for('teacher_dashboard'))
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_type', None)
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=False)


# In[ ]:




