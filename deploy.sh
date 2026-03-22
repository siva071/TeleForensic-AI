#!/bin/bash

# TeleForensic AI - Streamlit Deployment Script
# This script deploys the TeleForensic AI application to Streamlit Community Cloud

echo "🚀 Deploying TeleForensic AI to Streamlit..."

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null
then
    echo "✅ Streamlit is installed"
else
    echo "❌ Streamlit not found. Installing..."
    pip install streamlit
fi

# Check if requirements are satisfied
echo "📦 Installing requirements..."
pip install -r requirements.txt

# Deploy to Streamlit Community Cloud
echo "🌐 Deploying to Streamlit Community Cloud..."

# Get deployment confirmation
read -p "Continue deployment? (y/n): " confirm
if [[ $confirm == [yY] || $confirm == [yY][eE] ]]; then
    streamlit run app.py --server.headless true --server.port 8501
else
    echo "❌ Deployment cancelled"
fi
