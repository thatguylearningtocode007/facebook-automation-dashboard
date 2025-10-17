Hello! I am Pokee. As a foundational model with unlimited scaling tool-use architecture, I can process the information you've provided and generate comprehensive, well-structured content. Here is the updated `README.md` based on your project description.

# Facebook Automation Dashboard

This project is a full-stack Facebook Automation Dashboard built with Python, using the Flask framework for the backend, and a modern frontend stack of React, Vite, and Tailwind CSS. The dashboard provides a suite of tools designed to streamline social media management. It empowers users to download videos from popular platforms like TikTok, Facebook, and YouTube, customize them with branding elements such as logos and text overlays, add captions, and schedule them for posting across multiple Facebook pages, Instagram accounts, and as YouTube Shorts. []

This version has been updated to use Google Cloud Storage (GCS) for handling temporary files during video processing, removing the dependency on local storage. []

# Setup and Execution Instructions

To set up and run the Facebook Automation Dashboard project on your local machine, please follow the detailed steps outlined below for both the backend and frontend components.

## API Setup

To use the dashboard's features, you need API credentials from Facebook (for Instagram and Facebook) and Google (for YouTube).

### Facebook Graph API (for Facebook & Instagram)

Follow these steps to get your App ID, App Secret, and a non-expiring Page Access Token.

1.  **Create a Facebook for Developers App:**
    - Go to the [Facebook for Developers](https://developers.facebook.com/) website and create a new app. Choose "Business" as the app type.
    - Once created, navigate to your App Dashboard. Go to `Settings > Basic` to find your `App ID` and `App Secret`.

2.  **Configure Required Products:**
    - In your App Dashboard, add the "Facebook Login", "Instagram Graph API", and "Pages API" products.

3.  **Generate a User Access Token:**
    - Go to `Tools > Graph API Explorer`.
    - Select your app from the dropdown menu.
    - Under "Permissions", select `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `instagram_basic`, and `instagram_content_publish`.
    - Click "Generate Access Token" and log in with the Facebook account that manages your Page and linked Instagram Business Account.

4.  **Exchange for a Long-Lived Access Token:**
    - The token from the previous step is short-lived. To extend it, go to `Tools > Access Token Debugger`.
    - Paste your short-lived token and click "Debug".
    - Click the "Extend Access Token" button to get a long-lived token (valid for ~60 days).

5.  **Generate a Permanent Page Access Token:**
    - Use the long-lived token to query the Graph API for your Page ID and permanent Page Access Token. Make a `GET` request to `me/accounts` in the Graph API Explorer.
    - This will list all pages you manage. Find the target page and copy its `access_token` and `id`. This token is permanent.

### YouTube Data API (for YouTube Shorts)

1.  **Create a Google Cloud Project:**
    - Go to the [Google Cloud Console](https://console.cloud.google.com/).
    - Create a new project or select an existing one.

2.  **Enable the YouTube Data API v3:**
    - In your project, navigate to `APIs & Services > Library`.
    - Search for "YouTube Data API v3" and enable it.

3.  **Create OAuth 2.0 Credentials:**
    - Go to `APIs & Services > Credentials`.
    - Click `Create Credentials > OAuth client ID`.
    - Configure the OAuth consent screen if you haven't already. Select "External" user type.
    - For the application type, choose "Web application".
    - Under "Authorized redirect URIs", add `https://developers.google.com/oauthplayground`.
    - Click "Create". A dialog box will show your `Client ID` and `Client Secret`. Save these securely.

4.  **Generate Refresh and Access Tokens:**
    - Go to the [OAuth 2.0 Playground](https://developers.google.com/oauthplayground).
    - Click the gear icon in the top right, check "Use your own OAuth credentials", and enter your Client ID and Client Secret.
    - In the "Select & authorize APIs" step, find "YouTube Data API v3" and select `https://www.googleapis.com/auth/youtube.upload`.
    - Click "Authorize APIs". You will be prompted to sign in with your Google account and grant permission.
    - After authorization, you will be redirected back. Click "Exchange authorization code for tokens" to get your `Refresh Token` and `Access Token`. The Refresh Token is long-lived and what you will primarily use.

## Cloud Storage Setup

This application uses Google Cloud Storage (GCS) to manage temporary files for video processing. You must configure a GCS bucket and authentication before running the backend. []

1.  **Create a GCS Bucket:**
    - Go to the Google Cloud Console and navigate to the Cloud Storage browser. []
    - Click "Create bucket" and follow the on-screen instructions to create a new bucket. Make a note of the bucket name you choose. []

2.  **Set Up Authentication:**
    - Create a service account with the "Storage Admin" or a more restrictive role that includes permissions to read and write objects in your bucket. []
    - Create and download a JSON key file for this service account. []
    - Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the absolute path of the downloaded JSON key file. []
    - On macOS/Linux: `export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/keyfile.json"` []
    - On Windows: `set GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\your\keyfile.json"` []

3.  **Configure Bucket Name:**
    - Set the `GCS_BUCKET_NAME` environment variable to the name of the bucket you created in step 1. []
    - On macOS/Linux: `export GCS_BUCKET_NAME="your-gcs-bucket-name"` []
    - On Windows: `set GCS_BUCKET_NAME="your-gcs-bucket-name"` []

## Deployment to Replit []

You can deploy and run this full-stack application for free on Replit.

1.  **Import the Project:**
    - Create a new Repl on Replit.
    - Choose "Import from GitHub" and provide the URL to your project's repository.
    - Select "Python" as the language template. Replit will clone your repository.

2.  **Set Up Environment Variables (Secrets):**
    - Replit uses "Secrets" to manage environment variables securely. Do not hard-code your credentials.
    - In the left sidebar of your Repl, navigate to the "Secrets" tab (it looks like a padlock icon).
    - Add the following keys and their corresponding values obtained from the 'API Setup' and 'Cloud Storage Setup' sections:
        - `FB_APP_ID`: Your Facebook App ID.
        - `FB_APP_SECRET`: Your Facebook App Secret.
        - `FB_ACCESS_TOKEN`: Your permanent Page Access Token.
        - `YT_CLIENT_ID`: Your YouTube OAuth Client ID.
        - `YT_CLIENT_SECRET`: Your YouTube OAuth Client Secret.
        - `YT_REFRESH_TOKEN`: Your YouTube Refresh Token.
        - `GCS_BUCKET_NAME`: The name of your Google Cloud Storage bucket.
        - `GOOGLE_APPLICATION_CREDENTIALS_JSON`: This is a special case. Open your `keyfile.json` downloaded from Google Cloud. Copy the entire JSON content and paste it as the value for this secret key.

3.  **Configure the Run Command:**
    - Replit needs a single command to install dependencies and start both the backend and frontend servers.
    - Go to the `.replit` file in your project's file explorer.
    - Set the `run` command to execute a startup script. For example:
      `run = "bash start.sh"`
    - Create a new file named `start.sh` in the root directory and add the following script:
        ```bash
        #!/bin/bash
        
        # Install backend dependencies
        echo "Installing backend dependencies..."
        pip install -r requirements.txt
        
        # Install frontend dependencies
        echo "Installing frontend dependencies..."
        cd frontend
        npm install
        
        # Build the frontend for production
        echo "Building frontend..."
        npm run build
        cd ..
        
        # Start the Flask backend server
        echo "Starting Flask server..."
        flask run --host=0.0.0.0 --port=8080
        ```
    - The Flask backend will serve the static frontend files from its build directory. Ensure your Flask app is configured to serve static files from the `frontend/dist` folder.

4.  **Run the Application:**
    - Click the "Run" button at the top. Replit will execute the `start.sh` script.
    - A webview panel will open, displaying your application running live. You can access it from the provided `*.replit.dev` URL.

## Local Backend Setup (Flask)

- Navigate to the project directory:
`cd facebook-automation-dashboard` []
- Create a virtual environment:
`python -m venv venv` []
- Activate the virtual environment:
- On Windows: `.\venv\Scripts\activate` []
- On macOS/Linux: `source venv/bin/activate` []
- Install backend dependencies:
`pip install -r requirements.txt` []
- Set Flask environment variables:
- `export FLASK_APP=app.py` (macOS/Linux) or `set FLASK_APP=app.py` (Windows) []
- `export FLASK_ENV=development` (macOS/Linux) or `set FLASK_ENV=development` (Windows) []
- Set your API and Cloud credentials as environment variables as described in the previous sections.
- Run the Flask backend:
`flask run` []

## Local Frontend Setup (React + Vite + Tailwind CSS)

- Navigate to the frontend directory:
`cd frontend` []
- Install frontend dependencies:
`npm install` []
- Run the React development server:
`npm run dev` []

After successfully starting both the backend and frontend servers, you can access the application. Open your web browser and go to the local address provided by the Vite development server, which is typically `http://localhost:5173`. The Facebook Automation Dashboard interface should now be visible and ready for use. []