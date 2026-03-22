# TeleForensic AI - Deployment Guide

## 🚀 Streamlit Community Cloud Deployment

### Prerequisites
- Python 3.8+ installed
- Streamlit account (free at [streamlit.io](https://streamlit.io))
- Git repository (recommended)

### Quick Deploy Method

#### Option 1: Streamlit Community Cloud (Recommended)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Deploy TeleForensic AI"
   git branch -M main
   git remote add origin https://github.com/yourusername/teleforensic-ai.git
   git push -u origin main
   ```

2. **Deploy to Streamlit**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Select `app.py` as main file
   - Click Deploy

3. **Configuration**
   - Set environment variables in Streamlit dashboard:
     - `GEMINI_API_KEY`: Your Gemini API key
     - `SECRET_KEY`: Your app secret key

#### Option 2: Local Deployment

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Locally**
   ```bash
   streamlit run app.py
   ```

3. **Access Application**
   - Open browser to: `http://localhost:8501`

#### Option 3: Using Deploy Script

1. **Make Script Executable**
   ```bash
   chmod +x deploy.sh
   ```

2. **Run Deployment**
   ```bash
   ./deploy.sh
   ```

### 🌐 Production Deployment Services

#### Streamlit Community Cloud
- **Cost**: Free tier available
- **URL**: `https://yourapp.streamlit.app`
- **Features**: Automatic scaling, SSL, custom domains
- **Limit**: Free tier has resource limits

#### Alternative Platforms

##### Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```

##### Render
```bash
# Install Render CLI
npm install -g render-cli

# Deploy
render login
render deploy
```

##### Heroku
```bash
# Install Heroku CLI
heroku login

# Create app
heroku create your-app-name

# Deploy
heroku buildpacks:set heroku/python
heroku config:set GEMINI_API_KEY=your_api_key
git push heroku main
```

### 🔧 Environment Configuration

#### Required Environment Variables
- `GEMINI_API_KEY`: Google Gemini API key
- `SECRET_KEY`: Application secret key
- `DATABASE_URL`: Database connection (if using external DB)

#### Optional Environment Variables
- `DEBUG`: Set to `false` for production
- `LOG_LEVEL`: Set to `INFO` or `ERROR`
- `MAX_FILE_SIZE`: Maximum upload size in MB

### 📋 Deployment Checklist

#### Pre-Deployment
- [ ] Test all features locally
- [ ] Verify API key works
- [ ] Check file upload functionality
- [ ] Test AI chatbot responses
- [ ] Verify map generation
- [ ] Test all analysis modules

#### Post-Deployment
- [ ] Verify app loads correctly
- [ ] Test file uploads in production
- [ ] Check AI responses work
- [ ] Verify maps display properly
- [ ] Test mobile responsiveness
- [ ] Monitor error logs
- [ ] Set up monitoring

### 🔍 Troubleshooting

#### Common Issues

**Memory Issues**
```python
# In app.py, add at top:
import gc
gc.enable()
```

**File Upload Errors**
```python
# Check file size limits
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
```

**API Rate Limits**
```python
# Add rate limiting
import time
time.sleep(1)  # Between API calls
```

**SSL/HTTPS Issues**
- Ensure all resources use HTTPS
- Check CORS settings
- Verify API endpoints

### 📊 Monitoring & Analytics

#### Streamlit Built-in
- App visits and usage
- Performance metrics
- Error tracking

#### External Monitoring
```python
# Add logging
import logging
logging.basicConfig(level=logging.INFO)
```

### 🔒 Security Considerations

#### API Key Security
- Never commit API keys to git
- Use environment variables
- Rotate keys regularly
- Monitor API usage

#### Input Validation
```python
# Sanitize user inputs
import re
def sanitize_input(text):
    return re.sub(r'[^\w\s-]', '', text)
```

### 📱 Mobile Optimization

#### Responsive Design
- Use Streamlit columns wisely
- Test on different screen sizes
- Optimize images for mobile

#### Performance
- Lazy load large datasets
- Use caching for expensive operations
```python
@st.cache_data
def expensive_operation(data):
    return process_data(data)
```

### 🔄 CI/CD Pipeline

#### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Streamlit

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Deploy to Streamlit
      run: |
        # Add your deployment commands here
```

### 📞 Support

#### Streamlit Documentation
- [Official Docs](https://docs.streamlit.io/)
- [Community Forums](https://discuss.streamlit.io/)
- [GitHub Issues](https://github.com/streamlit/streamlit/issues)

#### Deployment Help
- Check deployment logs
- Verify environment variables
- Test with sample data
- Monitor resource usage

---

**🎯 Next Steps:**
1. Choose deployment method
2. Configure environment variables
3. Deploy application
4. Test all features
5. Monitor performance

For issues, check the troubleshooting section or create an issue in your repository.
