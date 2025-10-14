from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import sqlite3
import hashlib
import os
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'pm-ajay-coordination-platform-secret-key'

# Database initialization
def init_database():
    conn = sqlite3.connect('pm_ajay.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            state TEXT,
            agency_type TEXT,
            full_name TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create projects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            component TEXT NOT NULL,
            state TEXT NOT NULL,
            agency_id INTEGER,
            budget REAL,
            status TEXT DEFAULT 'pending',
            start_date DATE,
            end_date DATE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (agency_id) REFERENCES users (id)
        )
    ''')
    
    # Create communications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS communications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id INTEGER,
            to_user_id INTEGER,
            message TEXT NOT NULL,
            subject TEXT,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_user_id) REFERENCES users (id),
            FOREIGN KEY (to_user_id) REFERENCES users (id)
        )
    ''')
    
    # Hash password function
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    # Insert sample users
    sample_users = [
        ('central_admin', hash_password('admin123'), 'central', None, None, 'Central Ministry Administrator', 'central.admin@gov.in'),
        ('up_admin', hash_password('state123'), 'state', 'uttar-pradesh', None, 'Uttar Pradesh State Administrator', 'up.admin@gov.in'),
        ('bihar_admin', hash_password('state123'), 'state', 'bihar', None, 'Bihar State Administrator', 'bihar.admin@gov.in'),
        ('agency_ngo1', hash_password('agency123'), 'agency', 'uttar-pradesh', 'ngo', 'Tribal Welfare NGO', 'ngo1@example.com'),
        ('agency_contractor1', hash_password('agency123'), 'agency', 'bihar', 'contractor', 'Construction Contractor Ltd', 'contractor1@example.com'),
    ]
    
    # Check if users already exist
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    if user_count == 0:
        cursor.executemany('''
            INSERT INTO users (username, password_hash, role, state, agency_type, full_name, email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', sample_users)
        
        # Insert sample projects
        sample_projects = [
            ('Tribal Hostel Construction Phase 1', 'hostel', 'uttar-pradesh', 4, 5000000, 'in_progress', '2024-01-15', '2024-12-31', 'Construction of residential facility for 200 tribal students'),
            ('Adarsh Gram Infrastructure Development', 'adarsh_gram', 'bihar', 5, 8000000, 'approved', '2024-02-01', '2024-11-30', 'Complete infrastructure development of model tribal village'),
            ('Education Support GIA Program', 'gia', 'uttar-pradesh', 4, 2000000, 'pending', '2024-03-01', '2024-08-31', 'Grant-in-aid for educational support programs'),
        ]
        
        cursor.executemany('''
            INSERT INTO projects (name, component, state, agency_id, budget, status, start_date, end_date, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_projects)
        
        # Insert sample communications
        sample_communications = [
            (1, 2, 'Budget approval required for Q2 projects in Uttar Pradesh. Please review and provide necessary documentation.', 'Budget Approval Request'),
            (2, 4, 'Project timeline needs to be updated. Please submit revised schedule by end of week.', 'Timeline Update Required'),
            (4, 2, 'Monthly progress report submitted. Hostel construction is 45% complete as of today.', 'Monthly Progress Report'),
        ]
        
        cursor.executemany('''
            INSERT INTO communications (from_user_id, to_user_id, message, subject)
            VALUES (?, ?, ?, ?)
        ''', sample_communications)
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

# Helper function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Helper function to get user by credentials
def authenticate_user(username, password):
    conn = sqlite3.connect('pm_ajay.db')
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    cursor.execute('''
        SELECT * FROM users WHERE username = ? AND password_hash = ?
    ''', (username, password_hash))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'role': user[3],
            'state': user[4],
            'agency_type': user[5],
            'full_name': user[6],
            'email': user[7]
        }
    return None

# Routes
@app.route('/')
def index():
    with open('index.html', 'r') as file:
        return file.read()

@app.route('/<path:filename>')
def static_files(filename):
    try:
        with open(filename, 'r') as file:
            content = file.read()
            if filename.endswith('.html'):
                return content, 200, {'Content-Type': 'text/html'}
            elif filename.endswith('.js'):
                return content, 200, {'Content-Type': 'application/javascript'}
            elif filename.endswith('.css'):
                return content, 200, {'Content-Type': 'text/css'}
            else:
                return content
    except FileNotFoundError:
        return "File not found", 404

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = authenticate_user(username, password)
    
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        return jsonify({
            'success': True,
            'user': user,
            'message': 'Login successful'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid credentials'
        }), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/dashboard/<role>')
def dashboard(role):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    username = session['username']
    user_role = session['role']
    
    # Get user details
    conn = sqlite3.connect('pm_ajay.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if role == 'central':
        return render_central_dashboard(cursor, user)
    elif role == 'state':
        return render_state_dashboard(cursor, user)
    elif role == 'agency':
        return render_agency_dashboard(cursor, user)
    else:
        return "Invalid role", 404

def render_central_dashboard(cursor, user):
    # Get all projects statistics
    cursor.execute('''
        SELECT component, COUNT(*), SUM(budget), state FROM projects 
        GROUP BY component, state ORDER BY state
    ''')
    project_stats = cursor.fetchall()
    
    # Get recent communications
    cursor.execute('''
        SELECT c.*, u.full_name as from_name FROM communications c
        JOIN users u ON c.from_user_id = u.id
        WHERE c.to_user_id = ? OR c.from_user_id = ?
        ORDER BY c.created_at DESC LIMIT 10
    ''', (user[0], user[0]))
    communications = cursor.fetchall()
    
    dashboard_html = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Central Ministry Dashboard | PM-AJAY</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://use.typekit.net/yjp3aho.css">
        <script src="https://unpkg.com/lucide@latest"></script>
        <style>body {{ font-family: "sofia-pro", sans-serif; }}</style>
    </head>
    <body class="bg-gray-50">
        <nav class="bg-white shadow-sm border-b border-gray-200">
            <div class="max-w-7xl mx-auto px-4">
                <div class="flex justify-between items-center h-16">
                    <div class="flex items-center<div class="flex items-center space-x-3">
                        <div class="w-10 h-10 bg-gradient-to-br from-red-600 to-red-700 rounded-lg flex items-center justify-center">
                            <i data-lucide="building-2" class="w-6 h-6 text-white"></i>
                        </div>
                        <div>
                            <div class="text-lg font-bold text-gray-900">Central Ministry Dashboard</div>
                            <div class="text-xs text-gray-500">Welcome, {user[6]}</div>
                        </div>
                    </div>
                    <div class="flex items-center space-x-4">
                        <button onclick="logout()" class="text-gray-700 hover:text-red-600 font-medium transition-colors">
                            <i data-lucide="log-out" class="w-5 h-5"></i>
                        </button>
                    </div>
                </div>
            </div>
        </nav>

        <div class="max-w-7xl mx-auto px-4 py-8">
            <!-- Dashboard Header -->
            <div class="mb-8">
                <h1 class="text-3xl font-bold text-gray-900 mb-2">National Overview</h1>
                <p class="text-gray-600">Monitor PM-AJAY implementation across all states and components</p>
            </div>

            <!-- Key Metrics -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div class="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-sm font-medium text-gray-600">Total Projects</p>
                            <p class="text-2xl font-bold text-gray-900">{len(project_stats)}</p>
                        </div>
                        <i data-lucide="folder" class="w-8 h-8 text-blue-500"></i>
                    </div>
                </div>
                <div class="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-sm font-medium text-gray-600">Active States</p>
                            <p class="text-2xl font-bold text-gray-900">{len(set([stat[3] for stat in project_stats]))}</p>
                        </div>
                        <i data-lucide="map-pin" class="w-8 h-8 text-green-500"></i>
                    </div>
                </div>
                <div class="bg-white rounded-lg shadow p-6 border-l-4 border-orange-500">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-sm font-medium text-gray-600">Total Budget</p>
                            <p class="text-2xl font-bold text-gray-900">₹{sum([stat[2] or 0 for stat in project_stats])/10000000:.1f}Cr</p>
                        </div>
                        <i data-lucide="indian-rupee" class="w-8 h-8 text-orange-500"></i>
                    </div>
                </div>
                <div class="bg-white rounded-lg shadow p-6 border-l-4 border-purple-500">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-sm font-medium text-gray-600">Components</p>
                            <p class="text-2xl font-bold text-gray-900">3</p>
                        </div>
                        <i data-lucide="layers" class="w-8 h-8 text-purple-500"></i>
                    </div>
                </div>
            </div>

            <!-- Recent Communications -->
            <div class="bg-white rounded-lg shadow mb-8">
                <div class="p-6 border-b border-gray-200">
                    <h2 class="text-xl font-semibold text-gray-900">Recent Communications</h2>
                </div>
                <div class="p-6">
                    <div class="space-y-4">
                        {generate_communications_html(communications)}
                    </div>
                </div>
            </div>
        </div>

        <script>
            lucide.createIcons();
            
            function logout() {{
                fetch('/api/logout', {{ method: 'POST' }})
                .then(() => {{ window.location.href = '/'; }});
            }}
        </script>
    </body>
    </html>
    '''
    return dashboard_html

def render_state_dashboard(cursor, user):
    user_state = user[4]
    
    # Get state-specific projects
    cursor.execute('''
        SELECT * FROM projects WHERE state = ? ORDER BY created_at DESC
    ''', (user_state,))
    state_projects = cursor.fetchall()
    
    # Get agencies in state
    cursor.execute('''
        SELECT * FROM users WHERE role = 'agency' AND state = ?
    ''', (user_state,))
    agencies = cursor.fetchall()
    
    dashboard_html = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>State Dashboard | PM-AJAY</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://use.typekit.net/yjp3aho.css">
        <script src="https://unpkg.com/lucide@latest"></script>
        <style>body {{ font-family: "sofia-pro", sans-serif; }}</style>
    </head>
    <body class="bg-gray-50">
        <nav class="bg-white shadow-sm border-b border-gray-200">
            <div class="max-w-7xl mx-auto px-4">
                <div class="flex justify-between items-center h-16">
                    <div class="flex items-center space-x-3">
                        <div class="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center">
                            <i data-lucide="map-pin" class="w-6 h-6 text-white"></i>
                        </div>
                        <div>
                            <div class="text-lg font-bold text-gray-900">State Dashboard</div>
                            <div class="text-xs text-gray-500">{user[6]} - {user_state.replace('-', ' ').title()}</div>
                        </div>
                    </div>
                    <button onclick="logout()" class="text-gray-700 hover:text-blue-600 font-medium transition-colors">
                        <i data-lucide="log-out" class="w-5 h-5"></i>
                    </button>
                </div>
            </div>
        </nav>

        <div class="max-w-7xl mx-auto px-4 py-8">
            <div class="mb-8">
                <h1 class="text-3xl font-bold text-gray-900 mb-2">State Overview</h1>
                <p class="text-gray-600">Manage PM-AJAY projects and coordinate with agencies</p>
            </div>

            <!-- State Metrics -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">Active Projects</h3>
                    <p class="text-3xl font-bold text-blue-600">{len(state_projects)}</p>
                </div>
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">Registered Agencies</h3>
                    <p class="text-3xl font-bold text-green-600">{len(agencies)}</p>
                </div>
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">Total Budget</h3>
                    <p class="text-3xl font-bold text-orange-600">₹{sum([proj[5] or 0 for proj in state_projects])/10000000:.1f}Cr</p>
                </div>
            </div>

            <!-- Projects Table -->
            <div class="bg-white rounded-lg shadow">
                <div class="p-6 border-b border-gray-200">
                    <h2 class="text-xl font-semibold text-gray-900">State Projects</h2>
                </div>
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Project</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Component</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Budget</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                            {generate_projects_table_html(state_projects)}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <script>
            lucide.createIcons();
            function logout() {{
                fetch('/api/logout', {{ method: 'POST' }})
                .then(() => {{ window.location.href = '/'; }});
            }}
        </script>
    </body>
    </html>
    '''
    return dashboard_html

def render_agency_dashboard(cursor, user):
    user_id = user[0]
    
    # Get agency projects
    cursor.execute('''
        SELECT * FROM projects WHERE agency_id = ? ORDER BY created_at DESC
    ''', (user_id,))
    agency_projects = cursor.fetchall()
    
    dashboard_html = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Agency Dashboard | PM-AJAY</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://use.typekit.net/yjp3aho.css">
        <script src="https://unpkg.com/lucide@latest"></script>
        <style>body {{ font-family: "sofia-pro", sans-serif; }}</style>
    </head>
    <body class="bg-gray-50">
        <nav class="bg-white shadow-sm border-b border-gray-200">
            <div class="max-w-7xl mx-auto px-4">
                <div class="flex justify-between items-center h-16">
                    <div class="flex items-center space-x-3">
                        <div class="w-10 h-10 bg-gradient-to-br from-green-600 to-green-700 rounded-lg flex items-center justify-center">
                            <i data-lucide="users" class="w-6 h-6 text-white"></i>
                        </div>
                        <div>
                            <div class="text-lg font-bold text-gray-900">Agency Dashboard</div>
                            <div class="text-xs text-gray-500">{user[6]} ({user[5].upper()})</div>
                        </div>
                    </div>
                    <button onclick="logout()" class="text-gray-700 hover:text-green-600 font-medium transition-colors">
                        <i data-lucide="log-out" class="w-5 h-5"></i>
                    </button>
                </div>
            </div>
        </nav>

        <div class="max-w-7xl mx-auto px-4 py-8">
            <div class="mb-8">
                <h1 class="text-3xl font-bold text-gray-900 mb-2">Project Dashboard</h1>
                <p class="text-gray-600">Track your assigned projects and report progress</p>
            </div>

            <!-- Agency Metrics -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">Assigned Projects</h3>
                    <p class="text-3xl font-bold text-green-600">{len(agency_projects)}</p>
                </div>
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">In Progress</h3>
                    <p class="text-3xl font-bold text-blue-600">{len([p for p in agency_projects if p[6] == 'in_progress'])}</p>
                </div>
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">Total Value</h3>
                    <p class="text-3xl font-bold text-orange-600">₹{sum([proj[5] or 0 for proj in agency_projects])/10000000:.1f}Cr</p>
                </div>
            </div>

            <!-- Projects -->
            <div class="bg-white rounded-lg shadow">
                <div class="p-6 border-b border-gray-200">
                    <h2 class="text-xl font-semibold text-gray-900">My Projects</h2>
                </div>
                <div class="p-6">
                    {generate_agency_projects_html(agency_projects)}
                </div>
            </div>
        </div>

        <script>
            lucide.createIcons();
            function logout() {{
                fetch('/api/logout', {{ method: 'POST' }})
                .then(() => {{ window.location.href = '/'; }});
            }}
        </script>
    </body>
    </html>
    '''
    return dashboard_html

def generate_communications_html(communications):
    if not communications:
        return '<p class="text-gray-500 text-center py-4">No recent communications</p>'
    
    html = ''
    for comm in communications:
        html += f'''
        <div class="border border-gray-200 rounded-lg p-4">
            <div class="flex justify-between items-start mb-2">
                <h3 class="font-semibold text-gray-900">{comm[5] or 'No Subject'}</h3>
                <span class="text-xs text-gray-500">{comm[7][:16]}</span>
            </div>
            <p class="text-gray-700 text-sm mb-2">{comm[3][:200]}...</p>
            <p class="text-xs text-gray-500">From: {comm[8]}</p>
        </div>
        '''
    return html

def generate_projects_table_html(projects):
    if not projects:
        return '<tr><td colspan="4" class="px-6 py-4 text-center text-gray-500">No projects found</td></tr>'
    
    html = ''
    for project in projects:
        status_color = {
            'pending': 'bg-yellow-100 text-yellow-800',
            'approved': 'bg-blue-100 text-blue-800',
            'in_progress': 'bg-green-100 text-green-800',
            'completed': 'bg-gray-100 text-gray-800'
        }.get(project[6], 'bg-gray-100 text-gray-800')
        
        html += f'''
        <tr>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{project[1]}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{project[2].replace('_', ' ').title()}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">₹{(project[5] or 0)/1000000:.1f}L</td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full {status_color}">
                    {project[6].replace('_', ' ').title()}
                </span>
            </td>
        </tr>
        '''
    return html

def generate_agency_projects_html(projects):
    if not projects:
        return '<p class="text-gray-500 text-center py-4">No projects assigned</p>'
    
    html = ''
    for project in projects:
        status_color = {
            'pending': 'bg-yellow-100 text-yellow-800',
            'approved': 'bg-blue-100 text-blue-800', 
            'in_progress': 'bg-green-100 text-green-800',
            'completed': 'bg-gray-100 text-gray-800'
        }.get(project[6], 'bg-gray-100 text-gray-800')
        
        html += f'''
        <div class="border border-gray-200 rounded-lg p-6 mb-4">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <h3 class="text-lg font-semibold text-gray-900">{project[1]}</h3>
                    <p class="text-sm text-gray-600">{project[2].replace('_', ' ').title()} Component</p>
                </div>
                <span class="inline-flex px-3 py-1 text-sm font-semibold rounded-full {status_color}">
                    {project[6].replace('_', ' ').title()}
                </span>
            </div>
            <p class="text-gray-700 mb-4">{project[9] or 'No description available'}</p>
            <div class="grid grid-cols-2 gap-4 text-sm">
                <div>
                    <span class="font-medium text-gray-600">Budget:</span>
                    <span class="ml-2">₹{(project[5] or 0)/1000000:.1f} Lakhs</span>
                </div>
                <div>
                    <span class="font-medium text-gray-600">Timeline:</span>
                    <span class="ml-2">{project[7] or 'TBD'} - {project[8] or 'TBD'}</span>
                </div>
            </div>
        </div>
        '''
    return html

if __name__ == '__main__':
    app.run(debug=True)