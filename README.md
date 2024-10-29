## **Introduction**

**HCCA AI Vision Project : QHSE Monitoring & Object Detection Platform** is a project developed for the Human Resources Management System (HRMS) at PT. Salam Pacific Indonesia Lines. Its purpose is to manage employee safety reports, identification, and investigation processes. Additionally, the project features a chatbot to assist with managing system information and procedures.

## **Installation**

> Note: use `virtualenv` or `conda` for better practice. You can install it by using `pip install virtualenv` or `conda install -c conda-forge mamba`. This project developed using `Python 3.12.3`

Steps to install the project:

1. Clone this repository `git clone https://github.com/khanzafa/qhse-app.git` or click `Clone or Download` button and then click `Download ZIP`

2. Install system-level dependencies (Linux only)

   ```bash
   sudo apt-get update && sudo apt-get install ffmpeg libsm6 libxext6 libgl1 libpq-dev musl-dev -y
   ```

3. Install requirements

   For Windows
   ```bash
   pip install -r requirements.txt
   ```

   For Linux
   ```bash
   pip install -r linux-requirements.txt
   ```

4. Set the environment variable. Make a new file `.env` and fill it with the following code:

   [Mail Setup Tutorial link](https://mailtrap.io/blog/flask-send-email-gmail/)
   How to get Firefox profile:
   1. Open Firefox  
   2. Type about:profiles  
   3. Copy the Root Directory path of the selected profile  
   
   How to get edge profile path:
   1. Open Edge  
   2. Type edge://version  
   3. Copy profile path
      
   ```env
   # PostgreSQL database configuration for development
   DATABASE_URL=postgresql://postgres:YOUR_POSTGRES_PASSWORD@localhost/
   YOUR_DATABASE_NAME

   # Secret key for Flask, Generated from `sk.py`
   SECRET_KEY=YOUR_SECRET

   # Mail setup
   MAIL_USERNAME='mail@gmail.com'
   MAIL_PASSWORD='password'

   # Browser profile setup
   FIREFOX_PROFILE_DIR=
   EDGE_PROFILE_DIR=
   ```

5. Prepare the database

   ```bash
   flask db init
   flask db migrate
   flask upgrade
   ```

6. Run the project

   ```bash
    flask run
   ```
 
