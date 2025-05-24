@echo off
REM Runner for Clara_BE Django backend

REM Activate virtual environment if exists
IF EXIST venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Install dependencies
pip install -r requirements.txt

REM Apply migrations
python manage.py migrate

REM Run the development server
python manage.py runserver
