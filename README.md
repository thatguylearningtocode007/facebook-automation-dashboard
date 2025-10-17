Hello! I am Pokee. As a foundational model with unlimited scaling tool-use architecture, I can process the information you've provided and generate comprehensive, well-structured content. Here is the content based on your project description.

Facebook Automation Dashboard

This project is a full-stack Facebook Automation Dashboard built with Python, using the Flask framework for the backend, and a modern frontend stack of React, Vite, and Tailwind CSS. The dashboard provides a suite of tools designed to streamline social media management. It empowers users to download videos from popular platforms like TikTok, Facebook, and YouTube, customize them with branding elements such as logos and text overlays, add captions, and schedule them for posting across multiple Facebook pages and YouTube Shorts.

Setup and Execution Instructions

To set up and run the Facebook Automation Dashboard project on your local machine, please follow the detailed steps outlined below for both the backend and frontend components.

Backend Setup (Flask)

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
- Important: You will need to configure environment variables for your Facebook API credentials, such as `FB_APP_ID`, `FB_APP_SECRET`, and `FB_ACCESS_TOKEN`, as well as your YouTube API credentials. For guidance on obtaining these, consult the official documentation for the Facebook Graph API and the YouTube Data API.
- Run the Flask backend:
`flask run`

Frontend Setup (React + Vite + Tailwind CSS)

- Navigate to the frontend directory:
`cd frontend`
- Install frontend dependencies:
`npm install`
- Run the React development server:
`npm run dev`

After successfully starting both the backend and frontend servers, you can access the application. Open your web browser and go to the local address provided by the Vite development server, which is typically `http://localhost:5173`. The Facebook Automation Dashboard interface should now be visible and ready for use.