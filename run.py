#!/usr/bin/env python3

from app import app, db

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
        print("Starting Ekranų CRM application...")
        print("Visit http://localhost:5003 to access the application")
    
    app.run(host='0.0.0.0', port=5003, debug=True)