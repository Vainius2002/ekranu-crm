from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, date
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ekranu_crm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Models
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    contact_person = db.Column(db.String(100))
    company = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    campaigns = db.relationship('Campaign', backref='client', lazy=True, cascade='all, delete-orphan')

class Kampanija(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    client_brand_name = db.Column(db.String(200))
    campaign_name = db.Column(db.String(200))
    external_id = db.Column(db.String(100))  # To track source (projects_campaign_X)
    source_system = db.Column(db.String(50), default='projects-crm')  # Track which system it came from
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    budget = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    dooh_plans = db.relationship('DOOHPlan', backref='campaign', lazy=True, cascade='all, delete-orphan')

class DOOHPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    screen_bookings = db.relationship('ScreenBooking', backref='dooh_plan', lazy=True, cascade='all, delete-orphan')

class ScreenBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dooh_plan_id = db.Column(db.Integer, db.ForeignKey('dooh_plan.id'), nullable=False)
    screen_id = db.Column(db.Integer, db.ForeignKey('screen.id'), nullable=False)
    
    screen_slots = db.relationship('ScreenSlot', backref='booking', lazy=True, cascade='all, delete-orphan')

class ScreenSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('screen_booking.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    hour = db.Column(db.Integer, nullable=False)  # 0-23
    slots_purchased = db.Column(db.Integer, default=0)  # Number of ad slots purchased for this hour

class ScreenProvider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    contact_person = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    screens = db.relationship('Screen', backref='provider', lazy=True, cascade='all, delete-orphan')

class Screen(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('screen_provider.id'), nullable=False)
    
    # Basic info
    name = db.Column(db.String(100), nullable=False)
    image_path = db.Column(db.String(200))
    position_description = db.Column(db.Text)
    comment = db.Column(db.Text)
    
    # Screen type and parameters
    screen_type = db.Column(db.String(50), nullable=False)  # horizontal/vertical
    content_type = db.Column(db.String(50), nullable=False)  # video/static
    width = db.Column(db.Float, nullable=False)  # in meters
    height = db.Column(db.Float, nullable=False)  # in meters
    pixel_width = db.Column(db.Integer)
    pixel_height = db.Column(db.Integer)
    pixel_comment = db.Column(db.Text)
    
    # Location
    gps_latitude = db.Column(db.Float)
    gps_longitude = db.Column(db.Float)
    city = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    side = db.Column(db.String(10))  # D-right, K-left
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    pricing_hours = db.relationship('ScreenPricing', backref='screen', lazy=True, cascade='all, delete-orphan')
    bookings = db.relationship('ScreenBooking', backref='screen', lazy=True)

class ScreenPricing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    screen_id = db.Column(db.Integer, db.ForeignKey('screen.id'), nullable=False)
    hour = db.Column(db.Integer, nullable=False)  # 0-23
    price_per_thousand_contacts = db.Column(db.Float, nullable=False)
    contact_count = db.Column(db.Integer, nullable=False)
    
    __table_args__ = (db.UniqueConstraint('screen_id', 'hour'),)

# Routes
@app.route('/')
def index():
    providers = ScreenProvider.query.all()
    dooh_plans = DOOHPlan.query.all()
    screens = Screen.query.all()
    return render_template('index.html', providers=providers, dooh_plans=dooh_plans, screens=screens)

@app.route('/providers')
def providers():
    providers = ScreenProvider.query.all()
    return render_template('providers.html', providers=providers)

@app.route('/provider/new', methods=['GET', 'POST'])
def new_provider():
    if request.method == 'POST':
        provider = ScreenProvider(
            name=request.form['name'],
            email=request.form['email'],
            phone=request.form['phone'],
            contact_person=request.form['contact_person']
        )
        db.session.add(provider)
        db.session.commit()
        flash('Ekranų teikėjas sėkmingai pridėtas!')
        return redirect(url_for('providers'))
    return render_template('provider_form.html')

@app.route('/provider/<int:id>')
def provider_detail(id):
    provider = ScreenProvider.query.get_or_404(id)
    return render_template('provider_detail.html', provider=provider)

@app.route('/screens')
def screens():
    screens = Screen.query.all()
    return render_template('screens.html', screens=screens)

@app.route('/screen/new', methods=['GET', 'POST'])
def new_screen():
    if request.method == 'POST':
        # Handle image upload
        image_path = None
        if 'image' in request.files and request.files['image'].filename != '':
            image = request.files['image']
            if image:
                filename = secure_filename(image.filename)
                # Add timestamp to prevent filename conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                image_path = os.path.join('uploads', filename)
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(full_path)
        
        # Parse GPS coordinates
        gps_latitude = None
        gps_longitude = None
        if request.form.get('gps_coordinates'):
            try:
                coords = request.form['gps_coordinates'].strip()
                if ',' in coords:
                    lat_str, lng_str = coords.split(',', 1)
                    gps_latitude = float(lat_str.strip())
                    gps_longitude = float(lng_str.strip())
            except (ValueError, IndexError):
                flash('GPS koordinatės turi būti įvestos tinkamu formatu (pvz. 54.6872, 25.2797)', 'warning')
        
        screen = Screen(
            provider_id=request.form['provider_id'],
            name=request.form['name'],
            image_path=image_path,
            position_description=request.form['position_description'],
            comment=request.form['comment'],
            screen_type=request.form['screen_type'],
            content_type=request.form['content_type'],
            width=float(request.form['width']),
            height=float(request.form['height']),
            pixel_width=int(request.form['pixel_width']) if request.form['pixel_width'] else None,
            pixel_height=int(request.form['pixel_height']) if request.form['pixel_height'] else None,
            pixel_comment=request.form.get('pixel_comment'),
            gps_latitude=gps_latitude,
            gps_longitude=gps_longitude,
            city=request.form['city'],
            address=request.form['address'],
            side=request.form['side']
        )
        db.session.add(screen)
        db.session.commit()
        flash('Ekranas sėkmingai pridėtas!')
        return redirect(url_for('screens'))
    
    providers = ScreenProvider.query.all()
    return render_template('screen_form.html', providers=providers)

@app.route('/screen/<int:id>')
def screen_detail(id):
    screen = Screen.query.get_or_404(id)
    return render_template('screen_detail.html', screen=screen)

@app.route('/screen/<int:id>/pricing', methods=['GET', 'POST'])
def screen_pricing(id):
    screen = Screen.query.get_or_404(id)
    
    if request.method == 'POST':
        # Clear existing pricing
        ScreenPricing.query.filter_by(screen_id=id).delete()
        
        # Add new pricing for each hour
        for hour in range(24):
            price_field = f'price_{hour}'
            contact_field = f'contacts_{hour}'
            
            if price_field in request.form and contact_field in request.form:
                price = request.form[price_field]
                contacts = request.form[contact_field]
                
                if price and contacts:
                    pricing = ScreenPricing(
                        screen_id=id,
                        hour=hour,
                        price_per_thousand_contacts=float(price),
                        contact_count=int(contacts)
                    )
                    db.session.add(pricing)
        
        db.session.commit()
        flash('Įkainis sėkmingai atnaujintas!')
        return redirect(url_for('screen_detail', id=id))
    
    # Get existing pricing
    pricing_data = {}
    for pricing in screen.pricing_hours:
        pricing_data[pricing.hour] = {
            'price': pricing.price_per_thousand_contacts,
            'contacts': pricing.contact_count
        }
    
    return render_template('screen_pricing.html', screen=screen, pricing_data=pricing_data)

# API endpoints for dynamic client and campaign loading
@app.route('/api/clients')
def api_clients():
    clients = Client.query.all()
    return jsonify([{'id': c.id, 'name': c.name} for c in clients])

@app.route('/api/campaigns/<int:client_id>')
def api_campaigns_by_client(client_id):
    campaigns = Campaign.query.filter_by(client_id=client_id).all()
    return jsonify([{'id': c.id, 'name': c.name} for c in campaigns])

# DOOH Plan routes
@app.route('/dooh-plans')
def dooh_plans():
    plans = DOOHPlan.query.all()
    return render_template('dooh_plans.html', plans=plans)

@app.route('/api/campaigns/<int:client_id>')
def api_campaigns(client_id):
    """Get campaigns for a specific client"""
    campaigns = Campaign.query.filter_by(client_id=client_id).all()
    return jsonify([{
        'id': campaign.id,
        'name': campaign.name,
        'description': campaign.description
    } for campaign in campaigns])

@app.route('/dooh-plan/new', methods=['GET', 'POST'])
def new_dooh_plan():
    if request.method == 'POST':
        # Handle client creation or selection
        client_id = None
        
        # Traditional client handling (always required now)
        if request.form.get('client_type') == 'new':
            # Create new client
            client = Client(
                name=request.form['new_client_name'],
                email=request.form.get('new_client_email', ''),
                phone=request.form.get('new_client_phone', ''),
                contact_person=request.form.get('new_client_contact', ''),
                company=request.form.get('new_client_company', '')
            )
            db.session.add(client)
            db.session.flush()  # Get the ID without committing
            client_id = client.id
        else:
            # Use existing client
            client_id = request.form['existing_client_id']
        
        # Handle campaign creation or selection
        campaign_id = None
        campaign_type = request.form.get('campaign_type')
        
        if campaign_type == 'kampanija':
            # When using kampanija from projects-crm, extract the selected kampanija data from form
            kampanija_external_id = request.form['kampanija_id']  # This is the external_id from projects-crm
            
            # Get kampanija name from hidden form field
            kampanija_full_name = request.form.get('kampanija_full_name', '')
            kampanija_brand = request.form.get('kampanija_brand', '')
            kampanija_campaign = request.form.get('kampanija_campaign', '')
            
            # Use the kampanija name as campaign name
            campaign_name = kampanija_full_name if kampanija_full_name else f"Campaign {kampanija_external_id}"
            
            # Check if campaign already exists for this kampanija
            existing_campaign = Campaign.query.filter_by(
                client_id=client_id,
                name=campaign_name
            ).first()
            
            if existing_campaign:
                campaign_id = existing_campaign.id
            else:
                # Create new campaign from kampanija data
                campaign = Campaign(
                    client_id=client_id,
                    name=campaign_name,
                    description=f"Campaign from Projects CRM: {kampanija_brand} - {kampanija_campaign}",
                    budget=None  # Budget not available from projects CRM
                )
                db.session.add(campaign)
                db.session.flush()  # Get the ID without committing
                campaign_id = campaign.id
        elif campaign_type == 'new':
            # Create new campaign
            campaign = Campaign(
                client_id=client_id,
                name=request.form['new_campaign_name'],
                description=request.form.get('new_campaign_description', ''),
                start_date=datetime.strptime(request.form['campaign_start_date'], '%Y-%m-%d').date() if request.form.get('campaign_start_date') else None,
                end_date=datetime.strptime(request.form['campaign_end_date'], '%Y-%m-%d').date() if request.form.get('campaign_end_date') else None,
                budget=float(request.form['new_campaign_budget']) if request.form.get('new_campaign_budget') else None
            )
            db.session.add(campaign)
            db.session.flush()  # Get the ID without committing
            campaign_id = campaign.id
        else:
            # Use existing campaign
            campaign_id = request.form['existing_campaign_id']
        
        # Create the DOOH plan
        plan = DOOHPlan(
            campaign_id=campaign_id,
            name=request.form['name'],
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        )
        db.session.add(plan)
        db.session.commit()
        flash('DOOH planas sėkmingai sukurtas!')
        return redirect(url_for('dooh_plan_screens', id=plan.id))
    
    clients = Client.query.all()
    campaigns = Campaign.query.all()
    return render_template('dooh_plan_form.html', clients=clients, campaigns=campaigns)

@app.route('/dooh-plan/<int:id>')
def dooh_plan_detail(id):
    plan = DOOHPlan.query.get_or_404(id)
    return render_template('dooh_plan_detail.html', plan=plan)

@app.route('/dooh-plan/<int:id>/screens')
def dooh_plan_screens(id):
    plan = DOOHPlan.query.get_or_404(id)
    screens = Screen.query.all()
    return render_template('dooh_plan_screens.html', plan=plan, screens=screens)

@app.route('/dooh-plan/<int:plan_id>/add-screen/<int:screen_id>', methods=['POST'])
def add_screen_to_plan(plan_id, screen_id):
    plan = DOOHPlan.query.get_or_404(plan_id)
    screen = Screen.query.get_or_404(screen_id)
    
    # Check if screen is already in plan
    existing_booking = ScreenBooking.query.filter_by(dooh_plan_id=plan_id, screen_id=screen_id).first()
    if existing_booking:
        flash('Ekranas jau pridėtas į planą!')
        return redirect(url_for('dooh_plan_screens', id=plan_id))
    
    booking = ScreenBooking(dooh_plan_id=plan_id, screen_id=screen_id)
    db.session.add(booking)
    db.session.commit()
    flash(f'Ekranas "{screen.name}" pridėtas į planą!')
    return redirect(url_for('dooh_plan_screens', id=plan_id))

@app.route('/dooh-plan/<int:id>/media-plan')
def dooh_plan_media(id):
    plan = DOOHPlan.query.get_or_404(id)
    return render_template('dooh_media_plan.html', plan=plan)

# API Routes
@app.route('/api/import-brands', methods=['POST'])
def import_brands():
    """Import brands from agency-crm as clients"""
    # Check API key
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key != 'ekranu-crm-api-key':
        return jsonify({'error': 'Invalid API key'}), 401
    
    try:
        data = request.get_json()
        if not data or 'brands' not in data:
            return jsonify({'error': 'No brands data provided'}), 400
        
        imported_count = 0
        updated_count = 0
        
        for brand_data in data['brands']:
            # Check if client already exists (by external_id or name+company)
            existing_client = None
            
            # First try to find by external_id if provided
            if 'external_id' in brand_data:
                # We'll store external_id in the company field with a special prefix
                existing_client = Client.query.filter_by(
                    company=brand_data.get('company', ''),
                    name=brand_data['name']
                ).first()
            
            if existing_client:
                # Update existing client
                existing_client.email = brand_data.get('email', existing_client.email)
                existing_client.phone = brand_data.get('phone', existing_client.phone)
                existing_client.contact_person = brand_data.get('contact_person', existing_client.contact_person)
                updated_count += 1
            else:
                # Create new client
                new_client = Client(
                    name=brand_data['name'],
                    email=brand_data.get('email', ''),
                    phone=brand_data.get('phone', ''),
                    contact_person=brand_data.get('contact_person', ''),
                    company=brand_data.get('company', '')
                )
                db.session.add(new_client)
                imported_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'imported_count': imported_count,
            'updated_count': updated_count,
            'message': f'Successfully imported {imported_count} new brands and updated {updated_count} existing ones'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to import brands: {str(e)}'}), 500

@app.route('/api/clients', methods=['GET'])
def get_api_clients():
    """Get all clients for external systems"""
    # Check API key
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key != 'ekranu-crm-api-key':
        return jsonify({'error': 'Invalid API key'}), 401
    
    clients = Client.query.all()
    return jsonify([{
        'id': client.id,
        'name': client.name,
        'company': client.company,
        'email': client.email,
        'phone': client.phone,
        'contact_person': client.contact_person
    } for client in clients])

@app.route('/api/kampanijos', methods=['GET'])
def get_api_kampanijos():
    """Get all kampanijos for external systems"""
    # Check API key
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key != 'ekranu-crm-api-key':
        return jsonify({'error': 'Invalid API key'}), 401
    
    kampanijos = Kampanija.query.all()
    return jsonify([{
        'id': kampanija.id,
        'name': kampanija.name,
        'client_brand_name': kampanija.client_brand_name,
        'campaign_name': kampanija.campaign_name,
        'external_id': kampanija.external_id,
        'source_system': kampanija.source_system
    } for kampanija in kampanijos])

@app.route('/api/import-kampanijos', methods=['POST'])
def import_kampanijos():
    """Import kampanijos from projects-crm"""
    # Check API key
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key != 'ekranu-crm-api-key':
        return jsonify({'error': 'Invalid API key'}), 401
    
    try:
        data = request.get_json()
        if not data or 'kampanijos' not in data:
            return jsonify({'error': 'No kampanijos data provided'}), 400
        
        imported_count = 0
        updated_count = 0
        
        for kampanija_data in data['kampanijos']:
            # Check if kampanija already exists (by external_id)
            existing_kampanija = None
            if 'external_id' in kampanija_data:
                existing_kampanija = Kampanija.query.filter_by(
                    external_id=kampanija_data['external_id']
                ).first()
            
            if existing_kampanija:
                # Update existing kampanija
                existing_kampanija.name = kampanija_data['name']
                existing_kampanija.client_brand_name = kampanija_data.get('client_brand_name')
                existing_kampanija.campaign_name = kampanija_data.get('campaign_name')
                updated_count += 1
            else:
                # Create new kampanija
                new_kampanija = Kampanija(
                    name=kampanija_data['name'],
                    client_brand_name=kampanija_data.get('client_brand_name'),
                    campaign_name=kampanija_data.get('campaign_name'),
                    external_id=kampanija_data.get('external_id'),
                    source_system=kampanija_data.get('source_system', 'projects-crm')
                )
                db.session.add(new_kampanija)
                imported_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'imported_count': imported_count,
            'updated_count': updated_count,
            'message': f'Successfully imported {imported_count} new kampanijos and updated {updated_count} existing ones'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to import kampanijos: {str(e)}'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)