Hello! As Pokee, I can certainly update your `README.md` file with the detailed deployment instructions for Replit. Here is the revised content, incorporating the new section as requested.

# Facebook Automation Dashboard

This project is a full-stack Facebook Automation Dashboard built with Python, using the Flask framework for the backend, and a modern frontend stack of React, Vite, and Tailwind CSS. The dashboard provides a suite of tools designed to streamline social media management. It empowers users to download videos from popular platforms like TikTok, Facebook, and YouTube, customize them with branding elements such as logos and text overlays, add captions, and schedule them for posting across multiple Facebook pages, Facebook groups, and YouTube Shorts.

This version has been updated to use Google Cloud Storage (GCS) for handling temporary files during video processing and introduces a robust system for managing API tokens, posting targets, and post approvals.

# Setup and Execution Instructions

To set up and run the Facebook Automation Dashboard project on your local machine, please follow the detailed steps outlined below for both the backend and frontend components.

## Configuration Files

The application now uses two primary JSON files for configuration and state management:

- `config.json`: This file stores all your API tokens and posting targets. You will need to create and populate this file manually. It holds:
- Facebook Page Tokens
- Facebook Group Tokens
- YouTube Channel Tokens
- Lists of target Facebook Page IDs, Group IDs, and YouTube Channel IDs.

- `pending_posts.json`: This file is managed automatically by the application. It tracks posts submitted to Facebook groups that require admin approval. The application uses this file to monitor the approval status of each post.

## Cloud Storage Setup

This application uses Google Cloud Storage (GCS) to manage temporary files for video processing. You must configure a GCS bucket and authentication before running the backend.

1.  **Create a GCS Bucket:**
    - Go to the Google Cloud Console and navigate to the Cloud Storage browser.
    - Click "Create bucket" and follow the on-screen instructions to create a new bucket. Make a note of the bucket name you choose.

2.  **Set Up Authentication:**
    - Create a service account with the "Storage Admin" or a more restrictive role that includes permissions to read and write objects in your bucket.
    - Create and download a JSON key file for this service account.
    - Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the absolute path of the downloaded JSON key file.
    - On macOS/Linux: `export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/keyfile.json"`
    - On Windows: `set GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\your\keyfile.json"`

3.  **Configure Bucket Name:**
    - Set the `GCS_BUCKET_NAME` environment variable to the name of the bucket you created in step 1.
    - On macOS/Linux: `export GCS_BUCKET_NAME="your-gcs-bucket-name"`
    - On Windows: `set GCS_BUCKET_NAME="your-gcs-bucket-name"`

## Backend Setup (Flask)

- Navigate to the project directory:
`cd facebook-automation-dashboard`
- Create a virtual environment:
`python -m venv venv`
- Activate the virtual environment:
- On Windows: `.\venv\Scripts\activate`
- On macOS/Linux: `source venv/bin/activate`
- Install backend dependencies:
`pip install -r requirements.txt`
- Set Flask environment variables:
- `export FLASK_APP=app.py` (macOS/Linux) or `set FLASK_APP=app.py` (Windows)
- `export FLASK_ENV=development` (macOS/Linux) or `set FLASK_ENV=development` (Windows)
- Important: In addition to the cloud variables, you will need to configure your Facebook and YouTube API credentials in the `config.json` file. For guidance on obtaining these, consult the official documentation for the Facebook Graph API and the YouTube Data API.
- Run the Flask backend:
`flask run`

## Frontend Setup (React + Vite + Tailwind CSS)

- Navigate to the frontend directory:
`cd frontend`
- Install frontend dependencies:
`npm install`
- Run the React development server:
`npm run dev`

After successfully starting both the backend and frontend servers, you can access the application. Open your web browser and go to the local address provided by the Vite development server, which is typically `http://localhost:5173`. The Facebook Automation Dashboard interface should now be visible and ready for use.

# Deployment to a Free Web-Based Platform (Replit)

You can deploy and run this application for free on Replit. Follow these step-by-step instructions to get your dashboard live.

### 1. Import Repository from GitHub

- Log in to your Replit account.
- On the main dashboard, click the **+ Create Repl** button.
- In the creation modal, select the **Import from GitHub** tab.
- Paste the URL of your project's GitHub repository into the "GitHub URL" field.
- Replit will automatically detect the language (Python). Click **Import from GitHub** to begin the import process.

### 2. Configure Environment Variables (Secrets)

Replit uses a secure feature called "Secrets" to manage environment variables. Do not hardcode your API keys or credentials.

- In your Repl's workspace, navigate to the **Tools** section on the left sidebar and click on **Secrets**.
- You will add each required credential as a new secret. For each variable, enter the name in the "Key" field and the corresponding value in the "Value" field, then click **Add new secret**.

Add the following secrets:

- **`FACEBOOK_APP_ID`**: Your Facebook application ID.
- **`FACEBOOK_APP_SECRET`**: Your Facebook application secret.
- **`FACEBOOK_ACCESS_TOKEN`**: A long-lived access token for your Facebook account.
- **`YOUTUBE_API_KEY`**: Your Google Cloud project's YouTube Data API key.
- **`YOUTUBE_CLIENT_SECRET`**: Your OAuth 2.0 client secret from Google Cloud.
- **`YOUTUBE_CLIENT_ID`**: Your OAuth 2.0 client ID from Google Cloud.
- **`GCS_BUCKET_NAME`**: The name of your Google Cloud Storage bucket.
- **`GOOGLE_APPLICATION_CREDENTIALS_JSON`**: This is a special case. Open your downloaded `keyfile.json` from Google Cloud, copy its entire JSON content (including curly braces `{}`), and paste it directly into the "Value" field for this secret. Replit will handle it as a multi-line string.

### 3. Run Backend and Frontend Services

Replit can automatically detect and run your application, but for a dual-service setup (Flask backend and React frontend), you need to configure the `.replit` file to run both simultaneously.

- **Configure the `.replit` file:**
- In your Repl's file explorer, find and open the `.replit` file (if it's not visible, enable "Show hidden files" in the file explorer settings).
- Replace its content with the following configuration. This tells Replit to run the Flask backend and the React frontend in parallel.

```
# .replit
language = "python3"
entrypoint = "app.py"
run = "concurrently 'npm run dev --prefix frontend' 'flask run --host=0.0.0.0'"

[packager]
language = "python3"

  [packager.features]
  packageSearch = true
  guessImports = true
  enabledForHosting = false

[languages.python3]
pattern = "**/*.py"

  [languages.python3.languageServer]
  start = "pylsp"

[nix]
channel = "stable-23_11"

  [nix.deployment]
  # By default, we will attempt to use the Nix channel specified by the `channel`
  # field.
  #
  # If you want to use a different channel for deployments, you can specify it
  # here.
  channel = "stable-23_11"

# The command that is executed when the "Run" button is clicked.
[interpreter]
  [interpreter.command]
  # Generate a command that installs the packages in `replit.nix` and then
  # runs the `run` command.
  args = [
    "bash",
    "-c",
    "pkill -f 'npm run dev --prefix frontend' || true; pkill -f 'flask run' || true; pip install -r requirements.txt; npm install --prefix frontend; concurrently 'npm run dev --prefix frontend' 'flask run --host=0.0.0.0'",
  ]

[[pins]]
# You can use this section to pin Nix packages.
#
# For example:
#
# package = "cowsay"
# version = "3.03"
#
# For more information, see https://docs.replit.com/programming-ide/nix-on-replit
# and https://nixos.org/manual/nixpkgs/stable/#chap-builtins.
#
# There are also some advanced options for pinning Nix packages. For instance,
# you can pin a package from a specific Nix channel.
#
# For example:
#
# package = "cowsay"
# from = "nixos-22_11"
#
# Or you can pin a package from a specific GitHub repository.
#
# For example:
#
# package = "cowsay"
# from = "github:NixOS/nixpkgs/nixos-22.11"
#
# Finally, you can also pin a local Nix file.
#
# For example:
#
# package = "my-package"
# path = "./my-package.nix"
path = "replit.nix"

# The `replit.nix` file is the entrypoint for the Nix environment. It is
# responsible for installing the packages that your project needs.
#
# For more information, see https://docs.replit.com/programming-ide/nix-on-replit
[env]
# You can use this section to set environment variables for your Repl.
#
# For example:
#
# VAR = "value"
#
# For more information, see https://docs.replit.com/programming-ide/storing-secrets-and-environment-variables
VITE_API_URL = "https://<your-repl-name>.<your-username>.repl.co"
```

- **Update Frontend Configuration:**
- Go to the `frontend/` directory and open the `.env` file (or create one if it doesn't exist).
- Add the following line, replacing `<your-repl-name>` and `<your-username>` with your actual Replit details. This tells your React app where to find the Flask backend.
`VITE_API_URL=https://<your-repl-name>.<your-username>.repl.co`

- **Start the Application:**
- Click the large **Run** button at the top of the Replit interface.
- Replit will first install all Python and Node.js dependencies, which may take a few minutes.
- Once dependencies are installed, it will execute the `run` command, starting both the Flask server and the Vite development server.
- A **WebView** tab will open, showing your React application. You can now use the dashboard, which is publicly accessible at your Repl's URL.

## API and Token Management

The backend exposes several new endpoints to manage API tokens and posting targets.

- **`/api/update-fb-token`**: Use this endpoint to add or update a Facebook token for a page or group.
- **`/api/update-yt-token`**: Use this endpoint to add or update a YouTube token.
- **`/api/save-config`**: This endpoint saves the current token and target configurations from memory to the `config.json` file.
- **`/api/remove-fb-group`**: Use this endpoint to remove a Facebook group from the posting list in `config.json`.

## Facebook Group Post Approval Workflow

The application includes an automated workflow to handle posts that require admin approval in Facebook groups.

- When a video is posted to a group, it is added to the `pending_posts.json` file.
- The system periodically checks the status of these pending posts.
- If a post is not approved by a group admin within 3 days, the application will automatically attempt to delete the post from the group.
- After the unapproved post is removed, the corresponding Facebook group ID is automatically removed from the posting list in `config.json` to prevent future posting attempts to that group.
- The frontend dashboard includes a "Live Logs" section to provide real-time feedback on posting status, approvals, and removals.