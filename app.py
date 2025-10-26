from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database initialization
def init_db():
    conn = sqlite3.connect('portfolio.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            read_status BOOLEAN DEFAULT FALSE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            image_url TEXT,
            live_url TEXT,
            source_url TEXT,
            technologies TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            proficiency INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

@app.route('/')
def index():
    """Serve the main portfolio page"""
    return send_from_directory('.', 'index.html')

@app.route('/admin')
def admin():
    """Serve the admin dashboard"""
    return send_from_directory('.', 'admin.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (images, CSS, JS)"""
    return send_from_directory('.', filename)

@app.route('/api/contact', methods=['POST'])
def submit_contact():
    """Handle contact form submissions"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'subject', 'message']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Save to database
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO contact_messages (name, email, subject, message)
            VALUES (?, ?, ?, ?)
        ''', (data['name'], data['email'], data['subject'], data['message']))
        conn.commit()
        conn.close()
        
        # Send email notification (optional - requires email configuration)
        # send_email_notification(data)
        
        return jsonify({
            'message': 'Message sent successfully!',
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contact', methods=['GET'])
def get_contact_messages():
    """Get all contact messages (admin endpoint)"""
    try:
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM contact_messages ORDER BY created_at DESC')
        messages = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        message_list = []
        for msg in messages:
            message_list.append({
                'id': msg[0],
                'name': msg[1],
                'email': msg[2],
                'subject': msg[3],
                'message': msg[4],
                'created_at': msg[5],
                'read_status': bool(msg[6])
            })
        
        return jsonify(message_list), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    try:
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM projects ORDER BY created_at DESC')
        projects = cursor.fetchall()
        conn.close()
        
        project_list = []
        for proj in projects:
            project_list.append({
                'id': proj[0],
                'title': proj[1],
                'description': proj[2],
                'image_url': proj[3],
                'live_url': proj[4],
                'source_url': proj[5],
                'technologies': proj[6].split(',') if proj[6] else [],
                'created_at': proj[7]
            })
        
        return jsonify(project_list), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects', methods=['POST'])
def add_project():
    """Add a new project"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title') or not data.get('description'):
            return jsonify({'error': 'Title and description are required'}), 400
        
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO projects (title, description, image_url, live_url, source_url, technologies)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['title'],
            data['description'],
            data.get('image_url', ''),
            data.get('live_url', ''),
            data.get('source_url', ''),
            ','.join(data.get('technologies', []))
        ))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Project added successfully'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/skills', methods=['GET'])
def get_skills():
    """Get all skills"""
    try:
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM skills ORDER BY category, proficiency DESC')
        skills = cursor.fetchall()
        conn.close()
        
        skill_list = []
        for skill in skills:
            skill_list.append({
                'id': skill[0],
                'name': skill[1],
                'category': skill[2],
                'proficiency': skill[3],
                'created_at': skill[4]
            })
        
        return jsonify(skill_list), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/skills', methods=['POST'])
def add_skill():
    """Add a new skill"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('category') or not data.get('proficiency'):
            return jsonify({'error': 'Name, category, and proficiency are required'}), 400
        
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO skills (name, category, proficiency)
            VALUES (?, ?, ?)
        ''', (data['name'], data['category'], data['proficiency']))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Skill added successfully'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file uploads"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            return jsonify({
                'message': 'File uploaded successfully',
                'filename': filename,
                'url': f'/uploads/{filename}'
            }), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get portfolio statistics"""
    try:
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        
        # Count messages
        cursor.execute('SELECT COUNT(*) FROM contact_messages')
        message_count = cursor.fetchone()[0]
        
        # Count unread messages
        cursor.execute('SELECT COUNT(*) FROM contact_messages WHERE read_status = FALSE')
        unread_count = cursor.fetchone()[0]
        
        # Count projects
        cursor.execute('SELECT COUNT(*) FROM projects')
        project_count = cursor.fetchone()[0]
        
        # Count skills
        cursor.execute('SELECT COUNT(*) FROM skills')
        skill_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_messages': message_count,
            'unread_messages': unread_count,
            'total_projects': project_count,
            'total_skills': skill_count
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def send_email_notification(data):
    """Send email notification for new contact messages"""
    # This is optional and requires email configuration
    # You can configure SMTP settings here
    pass

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 