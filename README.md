# NovelSync - Advanced Carbon Footprint Tracker

## Overview

NovelSync is the world's most advanced carbon footprint tracking platform, combining AI-powered insights with scientific accuracy to help individuals and organizations reduce their environmental impact. Built with Flask and integrated with Perplexity AI, NovelSync provides personalized sustainability recommendations based on real-time data and regional factors.

## Key Features

### Carbon Footprint Calculation
- **Multi-category tracking**: Transport, food, energy, and waste
- **Regional accuracy**: Location-specific carbon factors for precise calculations
- **Real-time weather integration**: Context-aware suggestions based on local conditions
- **Scientific methodology**: Based on peer-reviewed environmental research

### AI-Powered EcoBot Assistant
- **Perplexity Sonar Pro integration**: Advanced AI for personalized sustainability advice
- **Context-aware responses**: Considers location, weather, and user behavior
- **Interactive chat interface**: Natural conversation about environmental topics
- **Real-time suggestions**: Immediate actionable recommendations

### Advanced Analytics
- **Environmental impact metrics**: Trees saved, Earth equivalents, sustainability scores
- **Progress tracking**: Historical data and trend analysis
- **Goal setting**: Custom carbon reduction targets
- **Regional comparisons**: Global benchmarking and local insights

### Professional Design
- **Custom Radial font**: Professional, non-AI aesthetic
- **Responsive interface**: Optimized for all devices
- **Accessibility focused**: WCAG compliant design
- **Performance optimized**: Fast loading and smooth interactions

## Technology Stack

### Backend
- **Flask**: Python web framework
- **SQLite**: Lightweight database
- **Perplexity AI**: Advanced language model integration
- **OpenWeatherMap API**: Real-time weather data
- **Gunicorn**: Production WSGI server

### Frontend
- **HTML5/CSS3**: Modern web standards
- **JavaScript**: Interactive functionality
- **Bootstrap 5**: Responsive design framework
- **Chart.js**: Data visualization
- **Custom Radial font**: Professional typography

### Security
- **Environment variables**: Secure API key management
- **Input validation**: XSS and injection protection
- **HTTPS enforcement**: Secure data transmission
- **Content Security Policy**: Advanced security headers
- **Parameterized queries**: SQL injection prevention

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Git version control

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/tanayvasishtha/NovelSync.git
   cd NovelSync
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` file with your API keys:
   ```
   PERPLEXITY_API_KEY=your_perplexity_api_key_here
   OPENWEATHER_API_KEY=your_openweather_api_key_here
   SECRET_KEY=your-secret-key-here
   FLASK_ENV=development
   ```

5. **Initialize database**
   ```bash
   python -c "from app import init_db; init_db()"
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

   The application will be available at `http://localhost:5000`

## API Configuration

### Perplexity AI API
1. Visit [Perplexity AI](https://www.perplexity.ai/)
2. Sign up for an account
3. Navigate to API settings
4. Generate an API key (starts with `pplx-`)
5. Add to your `.env` file

### OpenWeatherMap API
1. Visit [OpenWeatherMap](https://openweathermap.org/)
2. Create a free account
3. Generate an API key
4. Add to your `.env` file

## Deployment

### Render Deployment

1. **Connect to Render**
   - Visit [render.com](https://render.com)
   - Sign up with GitHub account
   - Click "New +" → "Web Service"

2. **Configure build settings**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --config gunicorn.conf.py app:app`
   - **Environment**: Python 3

3. **Set environment variables**
   - `PERPLEXITY_API_KEY`: Your Perplexity AI key
   - `OPENWEATHER_API_KEY`: Your OpenWeatherMap key
   - `FLASK_ENV`: `production`
   - `SECRET_KEY`: Secure random string

4. **Deploy**
   - Connect your GitHub repository
   - Render will automatically deploy on push

### Alternative Platforms

**Railway**
- Automatic GitHub integration
- Free tier available
- Easy environment variable management

**Heroku**
- Classic Flask deployment
- Comprehensive documentation
- Built-in monitoring

**DigitalOcean App Platform**
- Scalable infrastructure
- Global CDN
- Advanced security features

## Security Features

### Data Protection
- **Environment variables**: All sensitive data stored securely
- **Input sanitization**: XSS and injection prevention
- **HTTPS enforcement**: Secure data transmission
- **Content Security Policy**: Advanced security headers

### API Security
- **Rate limiting**: Prevents abuse
- **Input validation**: Ensures data integrity
- **Error handling**: Secure error responses
- **Authentication**: Session-based security

### Database Security
- **Parameterized queries**: SQL injection prevention
- **Data encryption**: Sensitive data protection
- **Access control**: User-based permissions
- **Backup strategies**: Data recovery procedures

## Architecture

### Application Structure
```
NovelSync/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── gunicorn.conf.py      # Production server config
├── Dockerfile            # Container configuration
├── static/               # Static assets
│   ├── images/           # Application images
│   └── fonts/            # Custom Radial font
├── templates/            # HTML templates
│   ├── index.html        # Main application page
│   ├── blog.html         # Blog content page
│   ├── ecobot.html       # AI assistant interface
│   └── about.html        # About information
└── novelsync.db          # SQLite database
```

### Core Components

**Carbon Calculation Engine**
- Regional factor integration
- Multi-category analysis
- Scientific methodology
- Real-time processing

**AI Integration Layer**
- Perplexity API integration
- Context-aware responses
- Natural language processing
- Personalized recommendations

**Analytics System**
- User behavior tracking
- Environmental impact metrics
- Progress visualization
- Goal management

**Security Framework**
- Input validation
- XSS protection
- SQL injection prevention
- Secure headers

## Contributing

### Development Guidelines
1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature-name`
3. **Follow coding standards**: PEP 8 for Python
4. **Add tests**: Ensure functionality
5. **Submit pull request**: Detailed description

### Code Quality
- **Type hints**: Python type annotations
- **Documentation**: Comprehensive docstrings
- **Error handling**: Graceful failure management
- **Performance**: Optimized algorithms

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

### Documentation
- **API Reference**: Comprehensive endpoint documentation
- **User Guide**: Step-by-step usage instructions
- **Deployment Guide**: Platform-specific setup
- **Security Guide**: Best practices and recommendations

### Community
- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Community support and ideas
- **Contributions**: Code improvements and enhancements

## Roadmap

### Planned Features
- **Mobile application**: Native iOS and Android apps
- **Advanced analytics**: Machine learning insights
- **Social features**: Community challenges and sharing
- **Enterprise version**: Organization-wide tracking

### Technical Improvements
- **Microservices architecture**: Scalable backend
- **Real-time updates**: WebSocket integration
- **Advanced caching**: Redis implementation
- **Monitoring**: Comprehensive logging and metrics

## Acknowledgments

- **Perplexity AI**: Advanced language model integration
- **OpenWeatherMap**: Real-time weather data
- **Scientific community**: Carbon calculation methodologies
- **Open source contributors**: Community support and improvements

---

**NovelSync** - Empowering individuals to make informed environmental decisions through advanced technology and scientific accuracy. 