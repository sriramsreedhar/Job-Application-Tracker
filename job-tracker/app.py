# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///job_tracker.db'
app.config['UPLOAD_FOLDER'] = 'uploads/resumes'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize database
db = SQLAlchemy(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Model
class JobApplication(db.Model):
    __tablename__ = 'job_application'  # Explicitly set table name
    
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    application_link = db.Column(db.String(500))
    password = db.Column(db.String(128))  # Store password in plaintext now
    resume_path = db.Column(db.String(255))
    notes = db.Column(db.Text)
    status = db.Column(db.String(50), default='Applied')
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Routes
@app.route('/')
def index():
    applications = JobApplication.query.order_by(JobApplication.application_date.desc()).all()
    return render_template('dashboard.html', applications=applications)

@app.route('/application/new', methods=['GET', 'POST'])
def new_application():
    if request.method == 'POST':
        resume = request.files.get('resume')
        resume_path = None
        
        if resume and resume.filename:
            filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{resume.filename}"
            resume_path = os.path.join('uploads/resumes', filename)
            resume.save(resume_path)
        
        application = JobApplication(
            company=request.form['company'],
            position=request.form['position'],
            application_link=request.form['application_link'],
            password=request.form['password'],  # Store password directly
            resume_path=resume_path,
            notes=request.form['notes'],
            status=request.form['status']
        )
        
        db.session.add(application)
        db.session.commit()
        
        flash('Application added successfully!')
        return redirect(url_for('index'))
    
    return render_template('application_form.html')

@app.route('/application/<int:id>/edit', methods=['GET', 'POST'])
def edit_application(id):
    application = JobApplication.query.get_or_404(id)
    
    if request.method == 'POST':
        application.company = request.form['company']
        application.position = request.form['position']
        application.application_link = request.form['application_link']
        
        if request.form['password']:
            application.password = request.form['password']  # Update password directly
            
        resume = request.files.get('resume')
        if resume and resume.filename:
            if application.resume_path and os.path.exists(application.resume_path):
                os.remove(application.resume_path)
            
            filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{resume.filename}"
            resume_path = os.path.join('uploads/resumes', filename)
            resume.save(resume_path)
            application.resume_path = resume_path
            
        application.notes = request.form['notes']
        application.status = request.form['status']
        
        db.session.commit()
        flash('Application updated successfully!')
        return redirect(url_for('index'))
    
    return render_template('application_form.html', application=application)

@app.route('/application/<int:id>/delete')
def delete_application(id):
    application = JobApplication.query.get_or_404(id)
    
    if application.resume_path and os.path.exists(application.resume_path):
        os.remove(application.resume_path)
    
    db.session.delete(application)
    db.session.commit()
    
    flash('Application deleted successfully!')
    return redirect(url_for('index'))

@app.route('/uploads/resumes/<path:filename>')
def download_resume(filename):
    return send_from_directory('uploads/resumes', filename)

#def init_db():
    """Initialize the database by dropping all tables and creating them again"""
    #with app.app_context():
        # Drop all tables
        #db.drop_all()
        # Create all tables
        #db.create_all()

if __name__ == '__main__':
    # Initialize database
    #init_db()
    app.run(debug=True)
