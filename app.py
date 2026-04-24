#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
招聘求职网站主应用
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'job_recruitment_secret_key_2024'
app.config['UPLOAD_FOLDER'] = 'uploads/resumes'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx', 'txt'}

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def get_db_connection():
    conn = sqlite3.connect('job_recruitment.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            user_type TEXT NOT NULL,
            company_name TEXT,
            company_description TEXT,
            full_name TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            requirements TEXT NOT NULL,
            salary_range TEXT,
            location TEXT,
            job_type TEXT,
            experience_level TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            jobseeker_id INTEGER NOT NULL,
            resume_id INTEGER,
            status TEXT DEFAULT 'pending',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs (id),
            FOREIGN KEY (jobseeker_id) REFERENCES users (id),
            FOREIGN KEY (resume_id) REFERENCES resumes (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def create_notification(user_id, title, message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO notifications (user_id, title, message)
        VALUES (?, ?, ?)
    ''', (user_id, title, message))
    conn.commit()
    conn.close()


@app.route('/')
def index():
    conn = get_db_connection()
    jobs = conn.execute('''
        SELECT jobs.*, users.company_name 
        FROM jobs 
        JOIN users ON jobs.company_id = users.id 
        WHERE jobs.is_active = 1 
        ORDER BY jobs.created_at DESC 
        LIMIT 10
    ''').fetchall()
    conn.close()
    return render_template('index.html', jobs=jobs)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        user_type = request.form['user_type']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查用户名是否已存在
        existing_user = cursor.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if existing_user:
            flash('用户名已存在，请选择其他用户名', 'danger')
            conn.close()
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        
        if user_type == 'company':
            company_name = request.form['company_name']
            company_description = request.form['company_description']
            cursor.execute('''
                INSERT INTO users (username, password, email, user_type, company_name, company_description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, hashed_password, email, user_type, company_name, company_description))
        else:
            full_name = request.form['full_name']
            phone = request.form['phone']
            cursor.execute('''
                INSERT INTO users (username, password, email, user_type, full_name, phone)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, hashed_password, email, user_type, full_name, phone))
        
        conn.commit()
        conn.close()
        
        flash('注册成功！请登录', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_type'] = user['user_type']
            flash('登录成功！', 'success')
            
            if user['user_type'] == 'company':
                return redirect(url_for('company_dashboard'))
            else:
                return redirect(url_for('jobseeker_dashboard'))
        else:
            flash('用户名或密码错误', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('已退出登录', 'info')
    return redirect(url_for('index'))


@app.route('/company/dashboard')
def company_dashboard():
    if 'user_id' not in session or session['user_type'] != 'company':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    jobs = conn.execute('SELECT * FROM jobs WHERE company_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    
    # 获取收到的简历
    applications = conn.execute('''
        SELECT applications.*, jobs.title as job_title, users.full_name as applicant_name
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        JOIN users ON applications.jobseeker_id = users.id
        WHERE jobs.company_id = ?
        ORDER BY applications.applied_at DESC
    ''', (session['user_id'],)).fetchall()
    
    # 获取未读通知数量
    unread_count = conn.execute('SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0', (session['user_id'],)).fetchone()[0]
    conn.close()
    
    return render_template('company_dashboard.html', jobs=jobs, applications=applications, unread_count=unread_count)


@app.route('/company/job/new', methods=['GET', 'POST'])
def create_job():
    if 'user_id' not in session or session['user_type'] != 'company':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        requirements = request.form['requirements']
        salary_range = request.form['salary_range']
        location = request.form['location']
        job_type = request.form['job_type']
        experience_level = request.form['experience_level']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO jobs (title, company_id, description, requirements, salary_range, location, job_type, experience_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, session['user_id'], description, requirements, salary_range, location, job_type, experience_level))
        conn.commit()
        conn.close()
        
        flash('职位发布成功！', 'success')
        return redirect(url_for('company_dashboard'))
    
    return render_template('create_job.html')


@app.route('/job/<int:job_id>')
def job_detail(job_id):
    conn = get_db_connection()
    job = conn.execute('''
        SELECT jobs.*, users.company_name, users.company_description
        FROM jobs
        JOIN users ON jobs.company_id = users.id
        WHERE jobs.id = ?
    ''', (job_id,)).fetchone()
    conn.close()
    
    if job is None:
        flash('职位不存在', 'danger')
        return redirect(url_for('index'))
    
    return render_template('job_detail.html', job=job)


@app.route('/job/<int:job_id>/edit', methods=['GET', 'POST'])
def edit_job(job_id):
    if 'user_id' not in session or session['user_type'] != 'company':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    job = conn.execute('SELECT * FROM jobs WHERE id = ? AND company_id = ?', (job_id, session['user_id'])).fetchone()
    
    if job is None:
        conn.close()
        flash('职位不存在或您没有权限编辑', 'danger')
        return redirect(url_for('company_dashboard'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        requirements = request.form['requirements']
        salary_range = request.form['salary_range']
        location = request.form['location']
        job_type = request.form['job_type']
        experience_level = request.form['experience_level']
        is_active = 1 if request.form.get('is_active') else 0
        
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE jobs SET title = ?, description = ?, requirements = ?, salary_range = ?, 
            location = ?, job_type = ?, experience_level = ?, is_active = ?
            WHERE id = ?
        ''', (title, description, requirements, salary_range, location, job_type, experience_level, is_active, job_id))
        conn.commit()
        conn.close()
        
        flash('职位更新成功！', 'success')
        return redirect(url_for('company_dashboard'))
    
    conn.close()
    return render_template('edit_job.html', job=job)


@app.route('/jobseeker/dashboard')
def jobseeker_dashboard():
    if 'user_id' not in session or session['user_type'] != 'jobseeker':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # 获取用户的投递记录
    applications = conn.execute('''
        SELECT applications.*, jobs.title as job_title, jobs.location, users.company_name
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        JOIN users ON jobs.company_id = users.id
        WHERE applications.jobseeker_id = ?
        ORDER BY applications.applied_at DESC
    ''', (session['user_id'],)).fetchall()
    
    # 获取用户的简历
    resume = conn.execute('SELECT * FROM resumes WHERE user_id = ?', (session['user_id'],)).fetchone()
    
    # 获取未读通知数量
    unread_count = conn.execute('SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0', (session['user_id'],)).fetchone()[0]
    conn.close()
    
    return render_template('jobseeker_dashboard.html', applications=applications, resume=resume, unread_count=unread_count)


@app.route('/jobseeker/resume/upload', methods=['GET', 'POST'])
def upload_resume():
    if 'user_id' not in session or session['user_type'] != 'jobseeker':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('没有选择文件', 'danger')
            return redirect(request.url)
        
        file = request.files['resume']
        
        if file.filename == '':
            flash('没有选择文件', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            original_name = file.filename
            filename = secure_filename(f"{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 检查是否已有简历
            existing_resume = cursor.execute('SELECT id FROM resumes WHERE user_id = ?', (session['user_id'],)).fetchone()
            
            if existing_resume:
                # 更新现有简历
                old_resume = cursor.execute('SELECT * FROM resumes WHERE user_id = ?', (session['user_id'],)).fetchone()
                # 删除旧文件
                if os.path.exists(old_resume['file_path']):
                    os.remove(old_resume['file_path'])
                
                cursor.execute('''
                    UPDATE resumes SET filename = ?, original_name = ?, file_path = ?
                    WHERE user_id = ?
                ''', (filename, original_name, file_path, session['user_id']))
            else:
                # 创建新简历
                cursor.execute('''
                    INSERT INTO resumes (user_id, filename, original_name, file_path)
                    VALUES (?, ?, ?, ?)
                ''', (session['user_id'], filename, original_name, file_path))
            
            conn.commit()
            conn.close()
            
            flash('简历上传成功！', 'success')
            return redirect(url_for('jobseeker_dashboard'))
        else:
            flash('不支持的文件格式，请上传 pdf, doc, docx 或 txt 文件', 'danger')
    
    return render_template('upload_resume.html')


@app.route('/job/<int:job_id>/apply', methods=['GET', 'POST'])
def apply_job(job_id):
    if 'user_id' not in session or session['user_type'] != 'jobseeker':
        flash('请先登录', 'warning')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    job = conn.execute('SELECT * FROM jobs WHERE id = ? AND is_active = 1', (job_id,)).fetchone()
    
    if job is None:
        conn.close()
        flash('职位不存在或已关闭', 'danger')
        return redirect(url_for('index'))
    
    # 检查是否已投递
    existing_application = conn.execute('''
        SELECT id FROM applications WHERE job_id = ? AND jobseeker_id = ?
    ''', (job_id, session['user_id'])).fetchone()
    
    if existing_application:
        conn.close()
        flash('您已经投递过这个职位了', 'warning')
        return redirect(url_for('job_detail', job_id=job_id))
    
    # 检查是否有简历
    resume = conn.execute('SELECT * FROM resumes WHERE user_id = ?', (session['user_id'],)).fetchone()
    
    if resume is None:
        conn.close()
        flash('请先上传简历', 'warning')
        return redirect(url_for('upload_resume'))
    
    if request.method == 'POST':
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO applications (job_id, jobseeker_id, resume_id)
            VALUES (?, ?, ?)
        ''', (job_id, session['user_id'], resume['id']))
        
        # 给企业发送通知
        create_notification(job['company_id'], '新的简历投递', f'您发布的职位 "{job["title"]}" 收到了新的简历投递')
        
        # 给求职者发送通知
        create_notification(session['user_id'], '投递成功', f'您已成功投递职位 "{job["title"]}"')
        
        conn.commit()
        conn.close()
        
        flash('投递成功！', 'success')
        return redirect(url_for('jobseeker_dashboard'))
    
    conn.close()
    return render_template('apply_job.html', job=job, resume=resume)


@app.route('/jobs')
def job_list():
    conn = get_db_connection()
    
    # 获取搜索和筛选参数
    keyword = request.args.get('keyword', '')
    location = request.args.get('location', '')
    job_type = request.args.get('job_type', '')
    experience_level = request.args.get('experience_level', '')
    
    query = '''
        SELECT jobs.*, users.company_name 
        FROM jobs 
        JOIN users ON jobs.company_id = users.id 
        WHERE jobs.is_active = 1
    '''
    params = []
    
    if keyword:
        query += ' AND (jobs.title LIKE ? OR jobs.description LIKE ? OR jobs.requirements LIKE ?)'
        params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
    
    if location:
        query += ' AND jobs.location LIKE ?'
        params.append(f'%{location}%')
    
    if job_type:
        query += ' AND jobs.job_type = ?'
        params.append(job_type)
    
    if experience_level:
        query += ' AND jobs.experience_level = ?'
        params.append(experience_level)
    
    query += ' ORDER BY jobs.created_at DESC'
    
    jobs = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('job_list.html', jobs=jobs, keyword=keyword, location=location, job_type=job_type, experience_level=experience_level)


@app.route('/notifications')
def notifications():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    notifications_list = conn.execute('''
        SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC
    ''', (session['user_id'],)).fetchall()
    
    # 标记为已读
    cursor = conn.cursor()
    cursor.execute('UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0', (session['user_id'],))
    conn.commit()
    conn.close()
    
    return render_template('notifications.html', notifications=notifications_list)


@app.route('/application/<int:app_id>/status', methods=['POST'])
def update_application_status(app_id):
    if 'user_id' not in session or session['user_type'] != 'company':
        return redirect(url_for('login'))
    
    status = request.form['status']
    
    conn = get_db_connection()
    
    # 检查权限
    application = conn.execute('''
        SELECT applications.*, jobs.title, jobs.company_id
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        WHERE applications.id = ?
    ''', (app_id,)).fetchone()
    
    if application is None or application['company_id'] != session['user_id']:
        conn.close()
        flash('无权操作此申请', 'danger')
        return redirect(url_for('company_dashboard'))
    
    cursor = conn.cursor()
    cursor.execute('UPDATE applications SET status = ? WHERE id = ?', (status, app_id))
    
    # 给求职者发送通知
    status_texts = {
        'pending': '待处理',
        'reviewed': '已查看',
        'interview': '邀请面试',
        'accepted': '已录用',
        'rejected': '已拒绝'
    }
    
    create_notification(
        application['jobseeker_id'],
        '投递状态更新',
        f'您投递的职位 "{application["title"]}" 状态已更新为: {status_texts.get(status, status)}'
    )
    
    conn.commit()
    conn.close()
    
    flash('状态更新成功！', 'success')
    return redirect(url_for('company_dashboard'))


@app.route('/resume/download/<int:resume_id>')
def download_resume(resume_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    resume = conn.execute('SELECT * FROM resumes WHERE id = ?', (resume_id,)).fetchone()
    
    if resume is None:
        conn.close()
        flash('简历不存在', 'danger')
        return redirect(url_for('index'))
    
    # 检查权限：求职者只能下载自己的简历，企业可以下载投递到自己职位的简历
    if session['user_type'] == 'jobseeker' and resume['user_id'] != session['user_id']:
        conn.close()
        flash('无权下载此简历', 'danger')
        return redirect(url_for('jobseeker_dashboard'))
    
    if session['user_type'] == 'company':
        # 检查是否有投递到该企业职位的申请
        application = conn.execute('''
            SELECT a.id FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.resume_id = ? AND j.company_id = ?
        ''', (resume_id, session['user_id'])).fetchone()
        
        if application is None:
            conn.close()
            flash('无权下载此简历', 'danger')
            return redirect(url_for('company_dashboard'))
    
    conn.close()
    
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        resume['filename'],
        as_attachment=True,
        download_name=resume['original_name']
    )


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5002)
