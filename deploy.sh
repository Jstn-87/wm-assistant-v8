#!/bin/bash

# WM Assistant Vercel Deployment Script

echo "🚀 Deploying WM Assistant to Vercel..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Check if user is logged in to Vercel
if ! vercel whoami &> /dev/null; then
    echo "🔐 Please login to Vercel:"
    vercel login
fi

# Deploy to Vercel
echo "📦 Deploying to Vercel..."
vercel --prod

echo "✅ Deployment complete!"
echo "🌐 Your WM Assistant is now live on Vercel!"
echo ""
echo "📋 Next steps:"
echo "1. Set OPENAI_API_KEY environment variable in Vercel dashboard"
echo "2. Test your deployed application"
echo "3. Configure custom domain if needed"
echo ""
echo "🔗 Check your Vercel dashboard for the deployment URL"
