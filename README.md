# Clara Backend (Clara_BE)

This is the backend for the Clara project, built with Django and Django REST Framework.

## Prerequisites
- Python 3.10+
- pip (Python package manager)
- (Recommended) [virtualenv](https://virtualenv.pypa.io/en/latest/)

## Setup Instructions

1. **Clone the repository** (if you haven't already):
   ```sh
   git clone <your-repo-url>
   cd Clara_BE
   ```

2. **Create and activate a virtual environment** (optional but recommended):
   ```sh
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

   Note: The project now requires djangorestframework-simplejwt for JWT authentication. Make sure to install all dependencies before running the server.

4. **Set up environment variables:**
   - Create a `.env` file in the root directory (same level as `manage.py`).
   - Add your Gemini API key:
     ```env
     GEMINI_API_KEY=your_gemini_api_key_here
     ```

5. **Apply database migrations:**
   ```sh
   python manage.py migrate
   ```

6. **Run the development server:**
   ```sh
   python manage.py runserver
   ```

## Quick Start (Windows)
You can use the provided `run_clara.bat` file to set up and run the server with one command:

```bat
run_clara.bat
```

## API Endpoints

### Research Endpoints
- `/api/research/<name>/` (GET, POST): Research a politician by name. Returns research data, can force new research with POST.

### Authentication Endpoints
- `/api/auth/register/` - Register a new user (POST)
- `/api/auth/login/` - Login with username and password (POST)
- `/api/auth/token/refresh/` - Refresh an expired access token (POST)

## Notes
- Make sure to keep your `.env` file secure and never commit it to version control.
- For production, set `DEBUG = False` and configure `ALLOWED_HOSTS` in `clara/settings.py`.

---

For any issues, please contact the maintainer.
