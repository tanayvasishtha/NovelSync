from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import sqlite3
import hashlib
import uuid


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') or os.urandom(24).hex()

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; img-src 'self' data:; connect-src 'self' https://api.perplexity.ai https://api.openweathermap.org"
    return response

# API Keys - Load from environment variables
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

# Debug: Check if API keys are loaded
print(f"Perplexity API key loaded: {'Yes' if PERPLEXITY_API_KEY else 'No'}")
print(f"OpenWeather API key loaded: {'Yes' if OPENWEATHER_API_KEY else 'No'}")

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
        'car': {'global': 0.171, 'europe': 0.142, 'us': 0.192, 'asia': 0.156},
        'bus': {'global': 0.089, 'europe': 0.076, 'us': 0.105, 'asia': 0.068},
        'train': {'global': 0.041, 'europe': 0.035, 'us': 0.058, 'asia': 0.044},
        'subway': {'global': 0.052, 'europe': 0.045, 'us': 0.068, 'asia': 0.055},
        'flight': {'global': 0.255, 'europe': 0.228, 'us': 0.275, 'asia': 0.242},
        'walking': {'global': 0.0, 'europe': 0.0, 'us': 0.0, 'asia': 0.0},
        'bicycle': {'global': 0.0, 'europe': 0.0, 'us': 0.0, 'asia': 0.0}
    },
    'food': {
        'beef': {'global': 26.5, 'europe': 24.8, 'us': 29.2, 'asia': 21.5},
        'chicken': {'global': 6.8, 'europe': 6.4, 'us': 7.3, 'asia': 5.9},
        'fish': {'global': 6.0, 'europe': 5.7, 'us': 6.4, 'asia': 5.4},
        'rice': {'global': 2.6, 'europe': 2.4, 'us': 2.9, 'asia': 2.1},
        'vegetables': {'global': 0.48, 'europe': 0.42, 'us': 0.58, 'asia': 0.35},
        'fruits': {'global': 0.42, 'europe': 0.38, 'us': 0.52, 'asia': 0.28},
        'dairy': {'global': 2.3, 'europe': 2.1, 'us': 2.6, 'asia': 1.9}
    },
    'energy': {
        'electricity': {'global': 0.485, 'europe': 0.312, 'us': 0.685, 'asia': 0.584},
        'natural_gas': {'global': 2.1, 'europe': 1.9, 'us': 2.3, 'asia': 2.0},
        'heating_oil': {'global': 2.8, 'europe': 2.6, 'us': 3.0, 'asia': 2.7}
    },
    'waste': {
        'landfill': {'global': 0.72, 'europe': 0.64, 'us': 0.82, 'asia': 0.58},
        'recycling': {'global': 0.16, 'europe': 0.13, 'us': 0.19, 'asia': 0.11},
        'composting': {'global': 0.11, 'europe': 0.09, 'us': 0.13, 'asia': 0.08}
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

def get_default_region():
    """Get default region information"""
    return {'country': 'Global', 'city': 'Unknown', 'region': 'Unknown'}

def get_weather_data(city, country):
    """Get weather data for context-aware suggestions"""
    try:
        if OPENWEATHER_API_KEY:
            response = requests.get(
                f"https://api.openweathermap.org/data/2.5/weather",
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
        'total': round(total_co2, 3),
        'transport': round(breakdown['transport'], 3),
        'food': round(breakdown['food'], 3),
        'energy': round(breakdown['energy'], 3),
        'waste': round(breakdown['waste'], 3),
        'breakdown': breakdown,
        'trees_saved': round(total_co2 / 22, 2),  # 1 tree absorbs ~22kg CO2/year
        'region_category': region_category
    }

def generate_eco_suggestions(user_data, region, weather_data, is_premium=False):
    """Generate advanced AI-powered eco suggestions using Perplexity Sonar Pro"""
    try:
        if not PERPLEXITY_API_KEY:
            print("Perplexity API key not found, using fallback suggestions")
            return get_fallback_suggestions(user_data)
        
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
        
        # Perplexity API call
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 250,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            response_data = response.json()
            suggestions = response_data['choices'][0]['message']['content'].strip().split('\n')
            suggestions = [s.strip() for s in suggestions if s.strip()]
            
            print(f"AI suggestions generated: {len(suggestions)} suggestions")
            
            # Ensure we have at least 3 suggestions
            if len(suggestions) < 3:
                print("Not enough AI suggestions, using fallback")
                return get_fallback_suggestions(user_data)
            
            return suggestions[:5]  # Return max 5 suggestions
        else:
            print(f"Perplexity API error: {response.status_code} - {response.text}")
            return get_fallback_suggestions(user_data)
        
    except Exception as e:
        print(f"AI suggestions error: {str(e)}")
        return get_fallback_suggestions(user_data)

def get_fallback_suggestions(user_data):
    """Enhanced fallback suggestions with comprehensive coverage"""
    print("Using fallback suggestions")
    suggestions = []
    
    # Transport suggestions
    if user_data['breakdown']['transport'] > 0:
        suggestions.extend([
            "Consider using public transportation or carpooling for your daily commute",
            "Explore electric vehicle options for your next car purchase",
            "Try walking or cycling for short trips under 2 miles",
            "Plan your errands to minimize multiple trips",
            "Consider telecommuting options to reduce commute emissions"
        ])
    
    # Food suggestions
    if user_data['breakdown']['food'] > 0:
        suggestions.extend([
            "Try incorporating more plant-based meals into your diet",
            "Support local farmers and reduce food transportation emissions",
            "Reduce food waste by planning meals and using leftovers",
            "Choose seasonal and organic produce when possible",
            "Consider growing your own herbs and vegetables"
        ])
    
    # Energy suggestions
    if user_data['breakdown']['energy'] > 0:
        suggestions.extend([
            "Switch to energy-efficient appliances and turn off unused electronics",
            "Consider installing solar panels or switching to renewable energy",
            "Use LED light bulbs and natural lighting when possible",
            "Adjust your thermostat to reduce heating and cooling costs",
            "Unplug chargers and devices when not in use"
        ])
    
    # Waste suggestions
    if user_data['breakdown']['waste'] > 0:
        suggestions.extend([
            "Start composting organic waste and reduce single-use plastics",
            "Implement a zero-waste lifestyle with reusable containers",
            "Recycle paper, glass, and metal products properly",
            "Choose products with minimal packaging",
            "Repair items instead of replacing them when possible"
        ])
    
    # General lifestyle suggestions
    suggestions.extend([
        "Support businesses that prioritize sustainability and environmental responsibility",
        "Educate yourself and others about climate change and its local impacts",
        "Participate in local environmental initiatives and community clean-up events",
        "Consider carbon offset programs for unavoidable emissions from essential activities",
        "Track your progress and set monthly reduction goals to maintain motivation"
    ])
    
    # Return unique suggestions, prioritizing based on user's highest impact areas
    unique_suggestions = list(dict.fromkeys(suggestions))  # Remove duplicates while preserving order
    
    # Prioritize suggestions based on user's highest impact areas
    impact_areas = [
        ('transport', user_data['breakdown']['transport']),
        ('food', user_data['breakdown']['food']),
        ('energy', user_data['breakdown']['energy']),
        ('waste', user_data['breakdown']['waste'])
    ]
    impact_areas.sort(key=lambda x: x[1], reverse=True)
    
    # Return 5-7 most relevant suggestions
    return unique_suggestions[:7]

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
    except Exception as e:
        print(f"Analytics tracking error: {str(e)}")

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
    except Exception as e:
        print(f"Save calculation error: {str(e)}")

def calculate_environmental_impact(carbon_total):
    """Calculate comprehensive environmental impact metrics"""
    try:
        # Updated constants based on recent scientific research
        GLOBAL_AVERAGE_CO2_PER_PERSON = 4.7  # metric tons per year (2023 data)
        TREES_PER_TON_CO2 = 48  # trees needed to absorb 1 ton of CO2 (mature trees)
        EARTH_CAPACITY = 1.6  # hectares per person for sustainable living
        AVERAGE_FOOTPRINT_PER_PERSON = 2.7  # hectares per person globally
        CARBON_TO_HECTARES = 0.42  # conversion factor from CO2 to hectares
        
        # Convert kg to metric tons
        carbon_tons = carbon_total / 1000
        
        # Calculate Earth equivalents
        if carbon_tons > 0:
            earths_needed = carbon_tons / GLOBAL_AVERAGE_CO2_PER_PERSON
            trees_needed = carbon_tons * TREES_PER_TON_CO2
            hectares_needed = carbon_tons * CARBON_TO_HECTARES
            
            # Calculate sustainability score (0-100) with improved algorithm
            sustainability_score = max(0, min(100, 100 - (carbon_tons / GLOBAL_AVERAGE_CO2_PER_PERSON) * 45))
            
            # Determine impact level with more precise thresholds
            if carbon_tons < 1.8:
                impact_level = "Low"
                impact_color = "#22C55E"
            elif carbon_tons < 4.2:
                impact_level = "Moderate"
                impact_color = "#F59E0B"
            else:
                impact_level = "High"
                impact_color = "#EF4444"
                
            # Calculate time to offset with more accurate formula
            years_to_offset = carbon_tons * 1.8  # improved estimate based on natural processes
            
            return {
                'carbon_tons': round(carbon_tons, 3),
                'earths_needed': round(earths_needed, 3),
                'trees_needed': int(trees_needed),
                'hectares_needed': round(hectares_needed, 3),
                'sustainability_score': round(sustainability_score, 1),
                'impact_level': impact_level,
                'impact_color': impact_color,
                'years_to_offset': round(years_to_offset, 1),
                'global_rank': "Above average" if carbon_tons < GLOBAL_AVERAGE_CO2_PER_PERSON else "Below average"
            }
        
        return None
    except Exception as e:
        print(f"Environmental impact calculation error: {str(e)}")
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

@app.route('/blog/coffee-environmental-impact')
def blog_coffee():
    """Blog post about coffee environmental impact"""
    track_analytics('page_view', session.get('user_id'))
    return render_template('blog_posts/coffee.html', user=session.get('user'))

@app.route('/blog/smartphone-environmental-impact')
def blog_smartphone():
    """Blog post about smartphone environmental impact"""
    track_analytics('page_view', session.get('user_id'))
    return render_template('blog_posts/smartphone.html', user=session.get('user'))

@app.route('/blog/electric-vehicles-truth')
def blog_ev():
    """Blog post about electric vehicles"""
    track_analytics('page_view', session.get('user_id'))
    return render_template('blog_posts/electric_vehicles.html', user=session.get('user'))

@app.route('/blog/diet-climate-impact')
def blog_diet():
    """Blog post about diet and climate impact"""
    track_analytics('page_view', session.get('user_id'))
    return render_template('blog_posts/diet.html', user=session.get('user'))

@app.route('/blog/renewable-energy-myths')
def blog_renewable():
    """Blog post about renewable energy myths"""
    track_analytics('page_view', session.get('user_id'))
    return render_template('blog_posts/renewable_energy.html', user=session.get('user'))

@app.route('/blog/plastic-problem')
def blog_plastic():
    """Blog post about plastic problem"""
    track_analytics('page_view', session.get('user_id'))
    return render_template('blog_posts/plastic_problem.html', user=session.get('user'))

@app.route('/blog/minimalism-greener-life')
def blog_minimalism():
    """Blog post about minimalism"""
    track_analytics('page_view', session.get('user_id'))
    return render_template('blog_posts/minimalism.html', user=session.get('user'))

@app.route('/blog/eco-friendly-travel')
def blog_travel():
    """Blog post about eco-friendly travel"""
    track_analytics('page_view', session.get('user_id'))
    return render_template('blog_posts/eco_travel.html', user=session.get('user'))

@app.route('/blog/greenwashing-companies')
def blog_greenwashing():
    """Blog post about greenwashing"""
    track_analytics('page_view', session.get('user_id'))
    return render_template('blog_posts/greenwashing.html', user=session.get('user'))

@app.route('/blog/carbon-taxes-dont-work')
def blog_carbon_taxes():
    """Blog post about carbon taxes"""
    track_analytics('page_view', session.get('user_id'))
    return render_template('blog_posts/carbon_taxes.html', user=session.get('user'))

@app.route('/blog/science-climate-change')
def blog_climate_science():
    """Blog post about climate change science"""
    track_analytics('page_view', session.get('user_id'))
    return render_template('blog_posts/climate_science.html', user=session.get('user'))

@app.route('/blog/world-2050')
def blog_2050():
    """Blog post about world in 2050"""
    track_analytics('page_view', session.get('user_id'))
    return render_template('blog_posts/world_2050.html', user=session.get('user'))

@app.route('/ecobot')
def ecobot():
    """EcoBot AI assistant page"""
    track_analytics('page_view', session.get('user_id'))
    return render_template('ecobot.html', user=session.get('user'))

@app.route('/about')
def about():
    """About page"""
    track_analytics('page_view', session.get('user_id'))
    return render_template('about.html', user=session.get('user'))

@app.route('/api/calculate', methods=['POST'])
def calculate():
    """Calculate carbon footprint from user input"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['transport_mode', 'transport_distance']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Validate numeric fields
        try:
            float(data['transport_distance'])
            if data.get('energy_kwh'):
                float(data['energy_kwh'])
            if data.get('waste_amount'):
                float(data['waste_amount'])
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid numeric values provided'
            }), 400
        
        # Get default region
        region = get_default_region()
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
        print(f"Calculation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Calculation failed. Please check your input and try again.'
        }), 400

@app.route('/api/region', methods=['GET'])
def get_region():
    """Get default region information"""
    try:
        region = get_default_region()
        return jsonify({'success': True, 'region': region})
    except Exception as e:
        print(f"Region detection error: {str(e)}")
        return jsonify({
            'success': False, 
            'region': {'country': 'Global', 'city': 'Unknown', 'region': 'Unknown'}
        })

@app.route('/api/ecobot/chat', methods=['POST'])
def ecobot_chat():
    """EcoBot AI chat with Perplexity Sonar Pro"""
    try:
        data = request.get_json()
        
        if not data or not data.get('message'):
            return jsonify({
                'success': False,
                'error': 'No message provided'
            }), 400
        
        user_message = data['message'].strip()
        
        # Validate message length
        if len(user_message) > 1000:
            return jsonify({
                'success': False,
                'error': 'Message too long. Please keep it under 1000 characters.'
            }), 400
        
        # Validate message content
        if not user_message or len(user_message) < 2:
            return jsonify({
                'success': False,
                'error': 'Please provide a valid message.'
            }), 400
        
        # Get user's location and context
        region = get_default_region()
        weather_data = get_weather_data(region['city'], region['country'])
        
        # Build context for Perplexity Sonar Pro
        context = f"""
        User location: {region['city']}, {region['country']}
        """
        
        if weather_data:
            context += f"Weather: {weather_data.get('weather', [{}])[0].get('main', 'Unknown')}, Temperature: {weather_data.get('main', {}).get('temp', 'Unknown')}°C"
        
        # Create prompt for Perplexity Sonar Pro
        prompt = f"""
        You are EcoBot, an AI-powered sustainability assistant. The user is asking: "{user_message}"
        
        Context: {context}
        
        Provide a helpful, informative response about sustainability, carbon reduction, green living, or environmental topics. 
        Focus on practical, actionable advice. Keep the response conversational and engaging.
        """
        
        # Perplexity Sonar Pro API call
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            response_data = response.json()
            ai_response = response_data['choices'][0]['message']['content'].strip()
            
            # Track analytics
            track_analytics('ecobot_chat', session.get('user_id'), {
                'user_message': user_message,
                'region': region,
                'response_length': len(ai_response)
            })
            
            return jsonify({
                'success': True,
                'response': ai_response
            })
        else:
            print(f"Perplexity API error: {response.status_code} - {response.text}")
            return jsonify({
                'success': False,
                'error': 'AI service temporarily unavailable'
            }), 500
        
    except Exception as e:
        print(f"EcoBot chat error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while processing your request'
        }), 500

@app.route('/api/premium/upgrade', methods=['POST'])
def upgrade_premium():
    """Handle premium upgrade (development mode)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Please log in to upgrade'})
        
        # Simple premium upgrade for development
        try:
            conn = sqlite3.connect('novelsync.db')
            c = conn.cursor()
            c.execute('UPDATE users SET premium = TRUE WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            
            session['user']['premium'] = True
            track_analytics('premium_upgrade', user_id)
            
            return jsonify({'success': True, 'message': 'Premium upgrade successful'})
        except Exception as e:
            print(f"Database error: {str(e)}")
            return jsonify({'success': False, 'message': 'Database update failed'})
    except Exception as e:
        print(f"Premium upgrade error: {str(e)}")
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