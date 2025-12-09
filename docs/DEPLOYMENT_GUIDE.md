# Deployment Guide: Firebase Hosting + Google Cloud Run

This guide covers deploying the Discovery Portal frontend to Firebase Hosting and the backend to Google Cloud Run.

## Overview

**Architecture:**
- **Frontend**: Angular SPA hosted on Firebase Hosting
- **Backend**: FastAPI application on Google Cloud Run
- **Authentication**: Firebase Authentication
- **Database**: PostgreSQL (managed or self-hosted)

## Prerequisites

- Firebase project created
- Google Cloud project created (can be same as Firebase project)
- Firebase CLI installed: `npm install -g firebase-tools`
- Google Cloud SDK installed: https://cloud.google.com/sdk/docs/install
- Docker installed (for local testing)

## Part 1: Backend Deployment to Cloud Run

### Step 1: Prepare Backend

Ensure your backend has:
- Firebase Admin SDK initialized
- Token validation middleware
- CORS configured for your domain
- Environment variables for database connection

### Step 2: Create Dockerfile

In your backend directory (`/workspaces/discovery`):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Step 3: Build and Push Docker Image

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export SERVICE_NAME="discovery-api"

# Configure Docker for Google Cloud
gcloud auth configure-docker

# Build the image
docker build -t gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest .

# Push to Google Container Registry
docker push gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest
```

### Step 4: Deploy to Cloud Run

```bash
# Deploy the service
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=your-database-url" \
  --set-env-vars "FIREBASE_PROJECT_ID=your-firebase-project-id" \
  --memory 512Mi \
  --max-instances 10
```

### Step 5: Note the Service URL

After deployment, Cloud Run will provide a URL like:
```
https://discovery-api-xxxxx-uc.a.run.app
```

Save this URL - you'll need it for frontend configuration.

### Step 6: Configure Cloud Run Service

```bash
# Allow unauthenticated access (protected by Firebase token validation)
gcloud run services add-iam-policy-binding ${SERVICE_NAME} \
  --region=${REGION} \
  --member="allUsers" \
  --role="roles/run.invoker"
```

## Part 2: Frontend Deployment to Firebase Hosting

### Step 1: Configure Firebase

1. Update `discoveryPortal/firebase.json`:

```json
{
  "hosting": {
    "public": "dist/discovery-portal/browser",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "/api/**",
        "run": {
          "serviceId": "discovery-api",
          "region": "us-central1"
        }
      },
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(js|css)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=31536000"
          }
        ]
      }
    ]
  }
}
```

2. Create `.firebaserc`:

```json
{
  "projects": {
    "default": "your-firebase-project-id"
  }
}
```

### Step 2: Update Environment Configuration

Edit `discoveryPortal/src/environments/environment.production.ts`:

```typescript
export const environment = {
  production: true,
  apiUrl: '/api',  // Firebase Hosting will proxy to Cloud Run
  firebase: {
    apiKey: 'YOUR_PROD_API_KEY',
    authDomain: 'your-project-id.firebaseapp.com',
    projectId: 'your-project-id',
    storageBucket: 'your-project-id.appspot.com',
    messagingSenderId: 'YOUR_MESSAGING_SENDER_ID',
    appId: 'YOUR_APP_ID'
  }
};
```

### Step 3: Build the Frontend

```bash
cd discoveryPortal

# Install dependencies (if not already done)
npm install

# Build for production
npm run build
```

This creates optimized production files in `dist/discovery-portal/browser/`.

### Step 4: Test Locally (Optional)

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login to Firebase
firebase login

# Test locally
firebase serve
```

Visit `http://localhost:5000` to test.

### Step 5: Deploy to Firebase Hosting

```bash
# Deploy to Firebase Hosting
firebase deploy --only hosting

# Or deploy specific project
firebase deploy --only hosting --project your-firebase-project-id
```

### Step 6: Access Your App

After deployment, your app will be available at:
- `https://your-project-id.web.app`
- `https://your-project-id.firebaseapp.com`

## Part 3: Configure Custom Domain (Optional)

### Step 1: Add Custom Domain in Firebase Console

1. Go to Firebase Console > Hosting
2. Click "Add custom domain"
3. Enter your domain (e.g., `discovery.yourdomain.com`)
4. Follow DNS configuration instructions

### Step 2: Update DNS Records

Add the following DNS records (values provided by Firebase):

```
Type: A
Name: discovery
Value: <Firebase IP addresses>

Type: TXT
Name: discovery
Value: <Verification code>
```

### Step 3: Wait for SSL Certificate

Firebase automatically provisions SSL certificate. This may take up to 24 hours.

## Part 4: Environment Variables & Secrets

### Backend Secrets (Cloud Run)

For sensitive data, use Google Secret Manager:

```bash
# Create secret
echo -n "your-database-password" | \
  gcloud secrets create db-password --data-file=-

# Grant Cloud Run access to secret
gcloud secrets add-iam-policy-binding db-password \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Deploy with secret
gcloud run deploy ${SERVICE_NAME} \
  --set-secrets="DATABASE_PASSWORD=db-password:latest"
```

#### Static API Key Authentication

The backend supports dual authentication: Firebase ID tokens (primary) and a static API key (fallback). This allows backend-to-backend communication or simple API access without Firebase.

**Generating a secure API key:**

```bash
# Generate a cryptographically secure API key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Setting the API key:**

1. For local development, add to `.env`:
   ```
   STATIC_API_KEY=your-generated-secure-key-here
   ```

2. For Cloud Run deployment:
   ```bash
   # Create secret
   python -c "import secrets; print(secrets.token_urlsafe(32))" | \
     gcloud secrets create static-api-key --data-file=-
   
   # Grant access
   gcloud secrets add-iam-policy-binding static-api-key \
     --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   
   # Deploy with secret
   gcloud run deploy ${SERVICE_NAME} \
     --set-secrets="STATIC_API_KEY=static-api-key:latest"
   ```

**Using the API key:**

Include the API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key-here" \
  https://your-backend-url/api/notebooks/search
```

**Security notes:**
- Keep the API key secret and rotate it periodically
- The API key grants full access to all resources (system-level permissions)
- For user-specific access, use Firebase authentication instead


### Frontend Environment Variables

For Firebase config, you can use:

1. **Environment files** (committed to repo - public API keys are safe)
2. **Build-time variables** (for CI/CD)
3. **Firebase Remote Config** (for runtime configuration)

## Part 5: CI/CD Setup (Optional)

### GitHub Actions for Frontend

Create `.github/workflows/deploy-frontend.yml`:

```yaml
name: Deploy to Firebase Hosting

on:
  push:
    branches:
      - main
    paths:
      - 'discoveryPortal/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      
      - name: Install dependencies
        working-directory: ./discoveryPortal
        run: npm ci
      
      - name: Build
        working-directory: ./discoveryPortal
        run: npm run build
      
      - name: Deploy to Firebase
        uses: FirebaseExtended/action-hosting-deploy@v0
        with:
          repoToken: '${{ secrets.GITHUB_TOKEN }}'
          firebaseServiceAccount: '${{ secrets.FIREBASE_SERVICE_ACCOUNT }}'
          projectId: your-firebase-project-id
          channelId: live
```

### GitHub Actions for Backend

Create `.github/workflows/deploy-backend.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches:
      - main
    paths:
      - 'src/**'
      - 'requirements.txt'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: your-gcp-project-id
      
      - name: Configure Docker
        run: gcloud auth configure-docker
      
      - name: Build Docker image
        run: |
          docker build -t gcr.io/${{ secrets.GCP_PROJECT_ID }}/discovery-api:${{ github.sha }} .
          docker push gcr.io/${{ secrets.GCP_PROJECT_ID }}/discovery-api:${{ github.sha }}
      
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy discovery-api \
            --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/discovery-api:${{ github.sha }} \
            --platform managed \
            --region us-central1 \
            --allow-unauthenticated
```

## Part 6: Monitoring & Logging

### Cloud Run Monitoring

```bash
# View logs
gcloud run services logs read ${SERVICE_NAME} --region ${REGION}

# View metrics in Cloud Console
# Go to Cloud Run > your-service > Metrics
```

### Firebase Hosting Monitoring

- View analytics in Firebase Console > Hosting
- Check bandwidth usage
- Monitor requests and errors

## Deployment Checklist

### Pre-Deployment

- [ ] Backend code tested locally
- [ ] Frontend code tested locally
- [ ] Firebase configuration added to environment files
- [ ] Database migrations applied
- [ ] Environment variables configured
- [ ] CORS settings verified

### Backend Deployment

- [ ] Docker image built and pushed
- [ ] Cloud Run service deployed
- [ ] Environment variables set
- [ ] Service URL noted
- [ ] Health check endpoint working
- [ ] Token validation tested

### Frontend Deployment

- [ ] Firebase project created
- [ ] firebase.json configured
- [ ] Production build successful
- [ ] Firebase Hosting deployed
- [ ] Custom domain configured (optional)
- [ ] SSL certificate active

### Post-Deployment

- [ ] Test login flow
- [ ] Verify API calls work
- [ ] Check user authentication
- [ ] Test all protected routes
- [ ] Monitor error logs
- [ ] Set up alerts

## Rollback Procedures

### Rollback Frontend

```bash
# List previous deployments
firebase hosting:releases:list

# Rollback to previous version
firebase hosting:clone SOURCE_SITE_ID:SOURCE_CHANNEL TARGET_SITE_ID:live
```

### Rollback Backend

```bash
# List revisions
gcloud run revisions list --service=${SERVICE_NAME} --region=${REGION}

# Route traffic to previous revision
gcloud run services update-traffic ${SERVICE_NAME} \
  --to-revisions=REVISION_NAME=100 \
  --region=${REGION}
```

## Cost Optimization

### Firebase Hosting
- Free tier: 10 GB storage, 360 MB/day transfer
- Paid: $0.026/GB for storage, $0.15/GB for transfer

### Cloud Run
- Free tier: 2 million requests/month
- Paid: $0.00002400 per request after free tier
- Use `--min-instances=0` to scale to zero when idle

### Database
- Consider Cloud SQL with automatic backups
- Use connection pooling
- Set appropriate instance size

## Troubleshooting

### Frontend Issues

**Build fails:**
- Check Node.js version (should be 18+)
- Clear node_modules and reinstall
- Check for TypeScript errors

**Can't access after deployment:**
- Verify firebase.json is correct
- Check rewrites configuration
- Verify custom domain DNS

### Backend Issues

**Cloud Run deployment fails:**
- Check Docker image builds locally
- Verify all dependencies in requirements.txt
- Check Cloud Run logs

**API returns 500:**
- Check environment variables
- Verify database connection
- Check Cloud Run logs
- Verify Firebase Admin SDK initialized

**CORS errors:**
- Update backend CORS to allow Firebase Hosting domain
- Verify preflight OPTIONS requests handled

## Support

- **Firebase Support**: https://firebase.google.com/support
- **Cloud Run Docs**: https://cloud.google.com/run/docs
- **Community**: Stack Overflow (tags: firebase, google-cloud-run)

## Summary

You now have:
- ✅ Backend deployed to Google Cloud Run
- ✅ Frontend deployed to Firebase Hosting
- ✅ Automatic SSL certificates
- ✅ Serverless scaling
- ✅ Integrated authentication
- ✅ Production-ready deployment

Your Discovery Portal is live and ready for users! 🚀
