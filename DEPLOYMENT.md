# WM Assistant - Vercel Deployment Guide

This guide will help you deploy the WM Assistant to Vercel.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **OpenAI API Key**: You'll need your OpenAI API key
3. **Git Repository**: Your code should be in a Git repository (GitHub, GitLab, or Bitbucket)

## Deployment Steps

### 1. Prepare Your Repository

Make sure your repository contains:
- `vercel.json` - Vercel configuration
- `requirements.txt` - Python dependencies
- `api/index.py` - Serverless function entry point
- `backend/` - Your Python backend code
- `frontend/public/` - Your frontend files

### 2. Deploy to Vercel

#### Option A: Deploy via Vercel CLI

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Login to Vercel:
   ```bash
   vercel login
   ```

3. Deploy from your project directory:
   ```bash
   vercel
   ```

4. Follow the prompts to configure your project

#### Option B: Deploy via Vercel Dashboard

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import your Git repository
4. Vercel will automatically detect the configuration

### 3. Set Environment Variables

In your Vercel dashboard:

1. Go to your project settings
2. Navigate to "Environment Variables"
3. Add the following variable:
   - **Name**: `OPENAI_API_KEY`
   - **Value**: Your OpenAI API key
   - **Environment**: Production, Preview, Development

### 4. Configure Domain (Optional)

1. In your Vercel dashboard, go to "Domains"
2. Add your custom domain if desired
3. Follow the DNS configuration instructions

## Project Structure

```
WM-Assistant_v8/
├── api/
│   └── index.py          # Vercel serverless function
├── backend/
│   ├── src/              # Python backend code
│   ├── support_database.json
│   └── requirements.txt
├── frontend/
│   └── public/           # Frontend files
├── vercel.json           # Vercel configuration
├── requirements.txt      # Python dependencies
└── .vercelignore        # Files to ignore during deployment
```

## Configuration Details

### vercel.json
- Routes all requests to the Python serverless function
- Sets maximum function duration to 30 seconds
- Configures environment variables

### API Endpoints
- `/api/chat` - Chat endpoint
- `/api/health` - Health check endpoint
- `/` - Serves the frontend application

## Troubleshooting

### Common Issues

1. **Function Timeout**: If responses take longer than 30 seconds, consider optimizing your code or using a different deployment platform for the backend.

2. **Import Errors**: Make sure all dependencies are listed in `requirements.txt`

3. **Environment Variables**: Ensure `OPENAI_API_KEY` is set in Vercel dashboard

4. **File Size Limits**: Vercel has a 50MB limit for serverless functions. The current configuration should be well within this limit.

### Debugging

1. Check Vercel function logs in the dashboard
2. Use `vercel logs` command to view real-time logs
3. Test locally with `vercel dev`

## Performance Considerations

- **Cold Starts**: Serverless functions may have cold start delays
- **Memory Usage**: Monitor memory usage in Vercel dashboard
- **Response Times**: Keep responses under 30 seconds

## Security

- Never commit API keys to your repository
- Use Vercel's environment variables for sensitive data
- Consider implementing rate limiting for production use

## Monitoring

- Use Vercel's built-in analytics
- Monitor function execution times
- Set up alerts for errors

## Next Steps

After deployment:
1. Test all endpoints
2. Configure custom domain (if needed)
3. Set up monitoring and alerts
4. Consider implementing caching for better performance
