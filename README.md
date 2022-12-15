# Telegram bot "homework_bot"

### Description

- polls the Practicum.Homework API service every 10 minutes and checks the status of the homework submitted for review;
- when updating the status, it analyzes the API response and sends a corresponding notification to Telegram;
- loges own work and send a message about important problems to Telegram.

### Technology

Python 3.7

### For launch

Create and activate virtual environment
```
py -3.7 -m venv venv

source venv/Scripts/activate
```

- Install dependencies from requirements.txt file
```
pip install -r requirements.txt
```

### Author

NotMainCode

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
