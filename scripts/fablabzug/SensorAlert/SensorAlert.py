import smtplib
import json
import sqlite3
from sqlite3 import Error

# Configuration
config = None

# Read config
with open(r"<path>\SensorAlertConfig.json") as json_data_file:
    config = json.load(json_data_file)

# Read environment and create alert message
def read_current_environment_and_create_alert_message():
    # Get environment data from database
    conn = sqlite3.connect(config["database_path"])
    cursor = conn.cursor()
    cursor.execute("SELECT state FROM app_environmentmodel LIMIT 1")
    rows = cursor.fetchall()

    environmentJson = rows[0][0]
    environment = json.loads(environmentJson)
    sensorValues = environment["sensor"]["reported"]

    # Check if any value is outside configured range
    sensorAlertString = "Einer oder mehrere Werte sind ausserhalb des idealen Bereichs:\n"
    sensorConfiguration = config["sensors"]

    for sensor in sensorValues.items():
        sensorName = sensor[0]
        sensorValue = sensor[1]

        for sensorConfig in sensorConfiguration:
            if sensorConfig["name"] == sensorName:

                min = sensorConfig["min"]
                max = sensorConfig["max"]

                if sensorValue > max:
                    sensorAlertString += "{}: zu hoch {} (Max {})\n".format(sensorName, round(sensorValue, 1), max);
                elif sensorValue < min:
                    sensorAlertString += "{}: zu tief {} (Min {})\n".format(sensorName, round(sensorValue, 1), min);

    return sensorAlertString

# Sending email alert
gmail_user = config["email_account"]["email"]
gmail_password = config["email_account"]["password"]

sent_from = gmail_user
to = config["email_recipients"]
subject = 'Sensor Alarm'
body = read_current_environment_and_create_alert_message();

email_text = """\
From: %s
To: %s
Subject: %s

%s
""" % (sent_from, ", ".join(to), subject, body)

try:
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(gmail_user, gmail_password)
    server.sendmail(sent_from, to, email_text)
    server.close()

    print('Email sent!')
except:
    print('Something went wrong...')