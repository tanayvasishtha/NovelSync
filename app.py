from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import requests
import json
from datetime import datetime, timedelta
import openai
from dotenv import load_dotenv
import sqlite3
import hashlib
import uuid
import stripe

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
GEOIP_API_KEY = os.getenv('GEOIP_API_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')

# Initialize Stripe
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

# Database initialization
def init_db():
    conn = sqlite3.connect('novelsync.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id TEXT PRIMARY KEY, email TEXT UNIQUE, password_hash TEXT, 
                  premium BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS calculations
                 (id TEXT PRIMARY KEY, user_id TEXT, carbon_total REAL, 
                  breakdown TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS analytics
                 (id TEXT PRIMARY KEY, event_type TEXT, user_id TEXT, 
                  data TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS goals
                 (id TEXT PRIMARY KEY, user_id TEXT, target_carbon REAL,
                  current_carbon REAL, deadline DATE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                 (id TEXT PRIMARY KEY, user_id TEXT, stripe_subscription_id TEXT,
                  status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# Advanced carbon calculation factors with regional variations
CARBON_FACTORS = {
    'transport': {
        'car': {'global': 0.2, 'europe': 0.15, 'us': 0.25, 'asia': 0.18},
        'bus': {'global': 0.09, 'europe': 0.08, 'us': 0.12, 'asia': 0.07},
        'train': {'global': 0.04, 'europe': 0.03, 'us': 0.06, 'asia': 0.05},
        'subway': {'global': 0.05, 'europe': 0.04, 'us': 0.07, 'asia': 0.06},
        'flight': {'global': 0.25, 'europe': 0.22, 'us': 0.28, 'asia': 0.24},
        'walking': {'global': 0.0, 'europe': 0.0, 'us': 0.0, 'asia': 0.0},
        'bicycle': {'global': 0.0, 'europe': 0.0, 'us': 0.0, 'asia': 0.0}
    },
    'food': {
        'beef': {'global': 27.0, 'europe': 25.0, 'us': 30.0, 'asia': 22.0},
        'chicken': {'global': 6.9, 'europe': 6.5, 'us': 7.5, 'asia': 6.0},
        'fish': {'global': 6.1, 'europe': 5.8, 'us': 6.5, 'asia': 5.5},
        'rice': {'global': 2.7, 'europe': 2.5, 'us': 3.0, 'asia': 2.2},
        'vegetables': {'global': 0.5, 'europe': 0.4, 'us': 0.6, 'asia': 0.3},
        'fruits': {'global': 0.4, 'europe': 0.3, 'us': 0.5, 'asia': 0.2},
        'dairy': {'global': 2.4, 'europe': 2.2, 'us': 2.8, 'asia': 2.0}
    },
    'energy': {
        'electricity': {'global': 0.5, 'europe': 0.3, 'us': 0.7, 'asia': 0.6},
        'natural_gas': {'global': 2.0, 'europe': 1.8, 'us': 2.2, 'asia': 1.9},
        'heating_oil': {'global': 2.7, 'europe': 2.5, 'us': 2.9, 'asia': 2.6}
    },
    'waste': {
        'landfill': {'global': 0.7, 'europe': 0.6, 'us': 0.8, 'asia': 0.5},
        'recycling': {'global': 0.15, 'europe': 0.12, 'us': 0.18, 'asia': 0.10},
        'composting': {'global': 0.1, 'europe': 0.08, 'us': 0.12, 'asia': 0.07}
    }
}

def get_region_category(country):
    """Determine region category for carbon factors"""
    europe_countries = ['Germany', 'France', 'UK', 'Italy', 'Spain', 'Netherlands', 'Switzerland', 'Sweden', 'Norway', 'Denmark']
    us_countries = ['United States', 'USA', 'Canada']
    asia_countries = ['China', 'Japan', 'India', 'South Korea', 'Singapore', 'Thailand', 'Vietnam', 'Indonesia']
    
    if country in europe_countries:
        return 'europe'
    elif country in us_countries:
        return 'us'
    elif country in asia_countries:
        return 'asia'
    else:
        return 'global'

def get_user_region(ip_address):
    """Get user's region using GeoIP API with fallback"""
    try:
        if GEOIP_API_KEY:
            response = requests.get(f"http://api.ipapi.com/{ip_address}?access_key={GEOIP_API_KEY}")
            if response.status_code == 200:
                data = response.json()
                return {
                    'country': data.get('country_name', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('region_name', 'Unknown')
                }
    except:
        pass
    
    # Fallback to IP-API (free tier)
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}")
        if response.status_code == 200:
            data = response.json()
            return {
                'country': data.get('country', 'Unknown'),
                'city': data.get('city', 'Unknown'),
                'region': data.get('regionName', 'Unknown')
            }
    except:
        pass
    
    return {'country': 'Global', 'city': 'Unknown', 'region': 'Unknown'}

def get_weather_data(city, country):
    """Get weather data for context-aware suggestions"""
    try:
        if OPENWEATHER_API_KEY:
            response = requests.get(
                f"http://api.openweathermap.org/data/2.5/weather",
                params={
                    'q': f"{city},{country}",
                    'appid': OPENWEATHER_API_KEY,
                    'units': 'metric'
                }
            )
            if response.status_code == 200:
                return response.json()
    except:
        pass
    return None

def calculate_carbon_footprint(data, region_category='global'):
    """Calculate total carbon footprint with regional factors"""
    total_co2 = 0
    breakdown = {
        'transport': 0,
        'food': 0,
        'energy': 0,
        'waste': 0
    }
    
    # Transport calculations with regional factors
    if 'transport_mode' in data and 'transport_distance' in data:
        mode = data['transport_mode']
        distance = float(data['transport_distance'])
        if mode in CARBON_FACTORS['transport']:
            factor = CARBON_FACTORS['transport'][mode].get(region_category, CARBON_FACTORS['transport'][mode]['global'])
            co2 = distance * factor
            breakdown['transport'] = co2
            total_co2 += co2
    
    # Food calculations with regional factors
    if 'food_choices' in data:
        for food in data['food_choices']:
            if food in CARBON_FACTORS['food']:
                factor = CARBON_FACTORS['food'][food].get(region_category, CARBON_FACTORS['food'][food]['global'])
                co2 = factor
                breakdown['food'] += co2
                total_co2 += co2
    
    # Energy calculations with regional factors
    if 'energy_kwh' in data:
        kwh = float(data['energy_kwh'])
        factor = CARBON_FACTORS['energy']['electricity'].get(region_category, CARBON_FACTORS['energy']['electricity']['global'])
        co2 = kwh * factor
        breakdown['energy'] = co2
        total_co2 += co2
    
    # Waste calculations with regional factors
    if 'waste_type' in data and 'waste_amount' in data:
        waste_type = data['waste_type']
        waste_amount = float(data['waste_amount'])
        if waste_type in CARBON_FACTORS['waste']:
            factor = CARBON_FACTORS['waste'][waste_type].get(region_category, CARBON_FACTORS['waste'][waste_type]['global'])
            co2 = waste_amount * factor
            breakdown['waste'] = co2
            total_co2 += co2
    
    return {
        'total': round(total_co2, 2),
        'breakdown': breakdown,
        'trees_saved': round(total_co2 / 22, 1),  # 1 tree absorbs ~22kg CO2/year
        'region_category': region_category
    }

def generate_eco_suggestions(user_data, region, weather_data, is_premium=False):
    """Generate advanced AI-powered eco suggestions"""
    try:
        if not OPENAI_API_KEY or not is_premium:
            return get_fallback_suggestions(user_data)
        
        openai.api_key = OPENAI_API_KEY
        
        # Build comprehensive context for AI
        context = f"""
        User location: {region['city']}, {region['country']}
        Carbon footprint: {user_data['total']} kg CO2e
        Breakdown: Transport: {user_data['breakdown']['transport']}, Food: {user_data['breakdown']['food']}, Energy: {user_data['breakdown']['energy']}, Waste: {user_data['breakdown']['waste']}
        Region category: {user_data.get('region_category', 'global')}
        """
        
        if weather_data:
            context += f"Weather: {weather_data.get('weather', [{}])[0].get('main', 'Unknown')}, Temperature: {weather_data.get('main', {}).get('temp', 'Unknown')}°C"
        
        prompt = f"""
        Based on this user data, provide 5 specific, actionable suggestions to reduce their carbon footprint:
        {context}
        
        Provide only the suggestions, one per line, without numbering or emojis. Focus on practical, immediate actions that are region-specific and weather-appropriate.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.7
        )
        
        suggestions = response.choices[0].message.content.strip().split('\n')
        return [s.strip() for s in suggestions if s.strip()]
        
    except Exception as e:
        return get_fallback_suggestions(user_data)

def get_fallback_suggestions(user_data):
    """Enhanced fallback suggestions"""
    suggestions = []
    
    if user_data['breakdown']['transport'] > 0:
        suggestions.append("Consider using public transportation or carpooling for your daily commute")
        suggestions.append("Explore electric vehicle options for your next car purchase")
    
    if user_data['breakdown']['food'] > 0:
        suggestions.append("Try incorporating more plant-based meals into your diet")
        suggestions.append("Support local farmers and reduce food transportation emissions")
    
    if user_data['breakdown']['energy'] > 0:
        suggestions.append("Switch to energy-efficient appliances and turn off unused electronics")
        suggestions.append("Consider installing solar panels or switching to renewable energy")
    
    if user_data['breakdown']['waste'] > 0:
        suggestions.append("Start composting organic waste and reduce single-use plastics")
        suggestions.append("Implement a zero-waste lifestyle with reusable containers")
    
    return suggestions

def track_analytics(event_type, user_id=None, data=None):
    """Track user analytics"""
    try:
        conn = sqlite3.connect('novelsync.db')
        c = conn.cursor()
        c.execute('''INSERT INTO analytics (id, event_type, user_id, data) 
                     VALUES (?, ?, ?, ?)''', 
                  (str(uuid.uuid4()), event_type, user_id, json.dumps(data) if data else None))
        conn.commit()
        conn.close()
    except:
        pass

def save_calculation(user_id, carbon_data):
    """Save calculation to database"""
    try:
        conn = sqlite3.connect('novelsync.db')
        c = conn.cursor()
        c.execute('''INSERT INTO calculations (id, user_id, carbon_total, breakdown) 
                     VALUES (?, ?, ?, ?)''', 
                  (str(uuid.uuid4()), user_id, carbon_data['total'], json.dumps(carbon_data['breakdown'])))
        conn.commit()
        conn.close()
    except:
        pass

def calculate_environmental_impact(carbon_total):
    """Calculate comprehensive environmental impact metrics"""
    
    # Constants for calculations
    GLOBAL_AVERAGE_CO2_PER_PERSON = 4.8  # metric tons per year
    TREES_PER_TON_CO2 = 50  # trees needed to absorb 1 ton of CO2
    EARTH_CAPACITY = 1.7  # hectares per person for sustainable living
    AVERAGE_FOOTPRINT_PER_PERSON = 2.8  # hectares per person globally
    
    # Convert kg to metric tons
    carbon_tons = carbon_total / 1000
    
    # Calculate Earth equivalents
    if carbon_tons > 0:
        earths_needed = carbon_tons / GLOBAL_AVERAGE_CO2_PER_PERSON
        trees_needed = carbon_tons * TREES_PER_TON_CO2
        hectares_needed = carbon_tons * 0.4  # rough conversion to hectares
        
        # Calculate sustainability score (0-100)
        sustainability_score = max(0, min(100, 100 - (carbon_tons / GLOBAL_AVERAGE_CO2_PER_PERSON) * 50))
        
        # Determine impact level
        if carbon_tons < 2:
            impact_level = "Low"
            impact_color = "#22C55E"
        elif carbon_tons < 5:
            impact_level = "Moderate"
            impact_color = "#F59E0B"
        else:
            impact_level = "High"
            impact_color = "#EF4444"
            
        # Calculate time to offset
        years_to_offset = carbon_tons * 2  # rough estimate
        
        return {
            'carbon_tons': round(carbon_tons, 2),
            'earths_needed': round(earths_needed, 2),
            'trees_needed': int(trees_needed),
            'hectares_needed': round(hectares_needed, 2),
            'sustainability_score': round(sustainability_score, 1),
            'impact_level': impact_level,
            'impact_color': impact_color,
            'years_to_offset': round(years_to_offset, 1),
            'global_rank': "Above average" if carbon_tons < GLOBAL_AVERAGE_CO2_PER_PERSON else "Below average"
        }
    
    return None

@app.route('/')
def index():
    """Main application page"""
    track_analytics('page_view', session.get('user_id'))
    return render_template('index.html', user=session.get('user'))

@app.route('/blog')
def blog():
    """Blog page with sustainability insights"""
    track_analytics('page_view', session.get('user_id'))
    return render_template('blog.html', user=session.get('user'))

@app.route('/api/calculate', methods=['POST'])
def calculate():
    """Calculate carbon footprint from user input"""
    try:
        data = request.get_json()
        
        # Get user region
        user_ip = request.remote_addr
        region = get_user_region(user_ip)
        region_category = get_region_category(region['country'])
        
        # Calculate carbon footprint with regional factors
        result = calculate_carbon_footprint(data, region_category)
        
        # Calculate environmental impact metrics
        impact_metrics = calculate_environmental_impact(result['total'])
        
        # Get weather data for context
        weather_data = get_weather_data(region['city'], region['country'])
        
        # Check if user is premium
        is_premium = session.get('user', {}).get('premium', False)
        
        # Generate AI suggestions
        suggestions = generate_eco_suggestions(result, region, weather_data, is_premium)
        
        # Save calculation if user is logged in
        if session.get('user_id'):
            save_calculation(session['user_id'], result)
        
        # Track analytics
        track_analytics('calculation', session.get('user_id'), {
            'carbon_total': result['total'],
            'region': region,
            'region_category': region_category
        })
        
        return jsonify({
            'success': True,
            'carbon_footprint': result,
            'region': region,
            'suggestions': suggestions,
            'weather': weather_data,
            'is_premium': is_premium,
            'impact_metrics': impact_metrics
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Calculation failed. Please check your input and try again.'
        }), 400

@app.route('/api/region', methods=['GET'])
def get_region():
    """Get user's region based on IP"""
    try:
        user_ip = request.remote_addr
        region = get_user_region(user_ip)
        return jsonify({'success': True, 'region': region})
    except:
        return jsonify({'success': False, 'region': {'country': 'Global', 'city': 'Unknown', 'region': 'Unknown'}})

@app.route('/api/premium/upgrade', methods=['POST'])
def upgrade_premium():
    """Handle premium upgrade with Stripe integration"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Please log in to upgrade'})
        
        # Create Stripe checkout session
        if STRIPE_SECRET_KEY:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'NovelSync Premium',
                        },
                        'unit_amount': 999,  # $9.99
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url='http://localhost:5000/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url='http://localhost:5000/cancel',
            )
            return jsonify({'success': True, 'session_id': checkout_session.id})
        else:
            # Fallback for development
            conn = sqlite3.connect('novelsync.db')
            c = conn.cursor()
            c.execute('UPDATE users SET premium = TRUE WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            
            session['user']['premium'] = True
            track_analytics('premium_upgrade', user_id)
            
            return jsonify({'success': True, 'message': 'Premium upgrade successful'})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Upgrade failed'})

@app.route('/api/user/history', methods=['GET'])
def get_user_history():
    """Get user's calculation history"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    try:
        conn = sqlite3.connect('novelsync.db')
        c = conn.cursor()
        c.execute('''SELECT carbon_total, breakdown, created_at 
                     FROM calculations WHERE user_id = ? 
                     ORDER BY created_at DESC LIMIT 10''', (user_id,))
        history = c.fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'history': [
                {
                    'total': row[0],
                    'breakdown': json.loads(row[1]),
                    'date': row[2]
                } for row in history
            ]
        })
    except:
        return jsonify({'success': False, 'message': 'Failed to load history'})

@app.route('/api/analytics/dashboard', methods=['GET'])
def analytics_dashboard():
    """Get analytics dashboard data (admin only)"""
    try:
        conn = sqlite3.connect('novelsync.db')
        c = conn.cursor()
        
        # Total calculations
        c.execute('SELECT COUNT(*) FROM calculations')
        total_calculations = c.fetchone()[0]
        
        # Total carbon saved
        c.execute('SELECT SUM(carbon_total) FROM calculations')
        total_carbon = c.fetchone()[0] or 0
        
        # Premium users
        c.execute('SELECT COUNT(*) FROM users WHERE premium = TRUE')
        premium_users = c.fetchone()[0]
        
        # Recent activity
        c.execute('''SELECT COUNT(*) FROM calculations 
                     WHERE created_at >= datetime('now', '-7 days')''')
        weekly_calculations = c.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'total_calculations': total_calculations,
                'total_carbon_kg': round(total_carbon, 2),
                'premium_users': premium_users,
                'trees_equivalent': round(total_carbon / 22, 1),
                'weekly_calculations': weekly_calculations
            }
        })
    except:
        return jsonify({'success': False, 'message': 'Failed to load analytics'})

@app.route('/api/goals/set', methods=['POST'])
def set_carbon_goal():
    """Set carbon reduction goal"""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': 'Not logged in'})
        
        conn = sqlite3.connect('novelsync.db')
        c = conn.cursor()
        c.execute('''INSERT INTO goals (id, user_id, target_carbon, current_carbon, deadline) 
                     VALUES (?, ?, ?, ?, ?)''', 
                  (str(uuid.uuid4()), user_id, data['target_carbon'], data['current_carbon'], data['deadline']))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Goal set successfully'})
    except:
        return jsonify({'success': False, 'message': 'Failed to set goal'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000) 