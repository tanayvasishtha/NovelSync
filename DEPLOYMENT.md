# NovelSync Deployment Guide

## 🚀 Recommended: Railway Deployment

### Why Railway?
- ✅ **Free tier available**
- ✅ **Automatic deployments from GitHub**
- ✅ **Easy environment variable management**
- ✅ **Great for AI/ML applications**
- ✅ **Built-in HTTPS**
- ✅ **No credit card required for free tier**

### Deployment Steps:

1. **Go to [Railway.app](https://railway.app)**
2. **Sign up with your GitHub account**
3. **Click "New Project" → "Deploy from GitHub repo"**
4. **Select your `tanayvasishtha/NovelSync` repository**
5. **Railway will automatically detect it's a Python app**

### Environment Variables to Set:

In Railway dashboard, go to your project → Variables tab and add:

```
PERPLEXITY_API_KEY=your_perplexity_api_key_here
FLASK_ENV=production
```

### Alternative Deployment Options:

#### **2. Render**
- Free tier available
- Easy GitHub integration
- Good for Flask applications

**Steps:**
1. Go to [render.com](https://render.com)
2. Sign up and connect GitHub
3. Click "New Web Service"
4. Select your repository
5. Set build command: `pip install -r requirements.txt`
6. Set start command: `gunicorn --config gunicorn.conf.py app:app`
7. Add environment variables

#### **3. Heroku**
- Classic choice for Flask
- Good documentation
- Paid plans only now

**Steps:**
1. Install Heroku CLI
2. `heroku create novelsync-app`
3. `git push heroku main`
4. Set environment variables: `heroku config:set PERPLEXITY_API_KEY=your_key`

#### **4. DigitalOcean App Platform**
- Professional option
- Good performance
- Easy scaling

**Steps:**
1. Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
2. Connect GitHub repository
3. Configure build settings
4. Set environment variables

## 🔧 Pre-deployment Checklist:

- ✅ Flask app configured
- ✅ Gunicorn configuration ready
- ✅ Requirements.txt updated
- ✅ Dockerfile available
- ✅ Environment variables documented
- ✅ Static files properly organized
- ✅ Database (SQLite) will be created automatically

## 🌐 Post-deployment:

1. **Test all functionality:**
   - Carbon calculator
   - EcoBot AI chat
   - Blog page
   - About page

2. **Monitor logs** for any issues

3. **Set up custom domain** (optional)

4. **Configure analytics** (optional)

## 📝 Important Notes:

- **SQLite database** will be created automatically on first run
- **Static files** (fonts, images) are included in the repository
- **Perplexity API key** must be set as environment variable
- **Font files** are served from `/static/fonts/` directory

## 🚨 Security Considerations:

- Never commit API keys to GitHub
- Use environment variables for sensitive data
- Enable HTTPS in production
- Regular security updates

## 📊 Monitoring:

- Check Railway/Render/Heroku logs for errors
- Monitor API usage (Perplexity)
- Track application performance
- Set up alerts for downtime

---

**Ready to deploy! Choose Railway for the easiest experience.** 