# NovelSync

_No emojis. No gradients. No clutter. Just Swiss precision for everyone's carbon footprint._

## Overview

NovelSync is the minimalist global carbon tracker and optimizer. Instantly see your real carbon footprint, region-adjusted, and receive actionable AI-powered green suggestions—all in a flawless Swiss-inspired layout.

## Features

- Swiss-design: abundance of white space, outlined components, readable fonts. Absolutely no gradients or purple hues—just honest greens and clear whites.
- Emoji prohibition: There are absolutely zero emojis in the interface, the code, documentation, or commit messages. This is non-negotiable.
- Fast regional input: Transport, home energy, food, waste—validated, region-adaptive.
- Real-time carbon breakdown with error-proof, global-standard formulas.
- Beautiful, green Chart.js visualizations.
- AI eco-coach: OpenAI API for location- and habit-specific advice.
- Robust: App never breaks. If an API is down, user is gently informed and calculations continue with reasonable data. All feedback is plain, direct, and emoji-free.

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/novelsync
   cd novelsync
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure API keys:
   - Copy `env.example` to `.env`
   - Add your API keys to the `.env` file:
     - OpenAI API key for AI suggestions
     - OpenWeatherMap API key for weather context
     - GeoIP API key for region detection (optional)

4. Run the application:
   ```bash
   python app.py
   ```

5. Open your browser and visit `http://localhost:5000`

## Carbon Calculation Methods

NovelSync uses scientifically validated carbon factors:

- **Transport**: Car (0.2 kg CO₂e/km), Bus (0.09), Train (0.04), Subway (0.05), Flight (0.25)
- **Food**: Beef (27.0), Chicken (6.9), Fish (6.1), Rice (2.7), Vegetables (0.5), Dairy (2.4)
- **Energy**: Electricity (0.5 kg CO₂e/kWh), Natural Gas (2.0), Heating Oil (2.7)
- **Waste**: Landfill (0.7), Recycling (0.15), Composting (0.1)

All calculations are region-aware and adapt to local factors when available.

## API Integrations

- **OpenAI API**: Generates personalized, context-aware eco suggestions
- **OpenWeatherMap API**: Provides weather context for location-specific advice
- **GeoIP API**: Automatically detects user location for regional calculations
- **Fallback Systems**: Robust error handling ensures the app works even when APIs are unavailable

## Swiss Design Principles

- Color palette: #228B22 (active green), #E6F4EA (background), #F5F5F5 (light gray), #FFFFFF (white)
- Typography: Helvetica Neue, Arial, or Inter for maximum legibility
- Layout: Clean, outlined components with generous white space
- No gradients, shadows, or decorative elements
- Responsive design that works on all devices
- Accessibility-first approach with large touch targets and keyboard navigation

## Development

### Project Structure

```
novelsync/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── templates/         # HTML templates
│   └── index.html    # Main application interface
├── env.example       # Environment variables template
└── README.md         # This file
```

### Commit Protocol

Every major feature must be committed with a short, clear, emoji-free message stating exactly what changed:

- "Added input validation to all forms"
- "Completed AI suggestion module"
- "Finished error handling and fallbacks"
- "Created visualization dashboard"

### Testing

The application includes comprehensive error handling and fallback systems. All calculations are validated and bounded to reasonable limits.

## Global Reach

NovelSync works worldwide with:
- Automatic region detection via IP geolocation
- Fallback to global averages when regional data is unavailable
- Support for multiple languages and regional preferences
- Responsive design optimized for all screen sizes

## Performance

- Fast loading times (<2 seconds)
- Optimized for mobile and desktop
- Minimal dependencies for maximum reliability
- Efficient carbon calculations with real-time updates

## License

MIT License - for everyone, everywhere.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following Swiss design principles
4. Test thoroughly
5. Submit a pull request with a clear, emoji-free description

## Support

For issues or questions, please create an issue in the repository. All communication should be professional and emoji-free, maintaining the Swiss design philosophy.

---

Built for HackForge 2025 with Swiss precision and global impact. 