import os
import sys
import smtplib
import json
import sqlite3
from sqlite3 import Error
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Email strings
sensorAlertString = ""
sensorStatusString = ""

# Argument
sendStatusMail = False
if len(sys.argv) == 2 and sys.argv[1] == 'status':
    print('Status mail mode')
    sendStatusMail = True;

# Configuration
config = None

# Read config
script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
with open(script_dir + "/SensorAlertConfig.json") as json_data_file:
    config = json.load(json_data_file)

# Read environment and create alert message
def read_current_environment_and_create_alert_message():
    # Get environment data from database
    conn = sqlite3.connect(config["database_path"])
    cursor = conn.cursor()
    cursor.execute("SELECT state FROM app_environmentmodel ORDER BY timestamp DESC LIMIT 1")
    rows = cursor.fetchall()

    environmentJson = rows[0][0]
    environment = json.loads(environmentJson)
    sensorValues = environment["sensor"]["reported"]

    # Check if any value is outside configured range
    sensorConfiguration = config["sensors"]

    global sensorAlertString
    global sensorStatusString

    for sensor in sensorValues.items():
        sensorName = sensor[0]
        sensorValue = sensor[1]

        for sensorConfig in sensorConfiguration:
            if sensorConfig["name"] == sensorName:

                min = sensorConfig["min"]
                max = sensorConfig["max"]

                if type(sensorValue) != float:
                    sensorStatusString += "{}: kein Wert {} (Min {}, Max {})\n".format(sensorName, sensorValue, min, max);
                else:
                    if sensorValue > max:
                        sensorAlertString += "{}: zu hoch {} (Min {}, Max {})\n".format(sensorName, sensorValue, min, max);
                    elif sensorValue < min:
                        sensorAlertString += "{}: zu tief {} (Min {}, Max {})\n".format(sensorName, sensorValue, min, max);
                    else:
                        sensorStatusString += "{}: OK {} (Min {}, Max {})\n".format(sensorName, sensorValue, min, max);

    return "Werte ausserhalb des idealen Bereichs:\n\n" + sensorAlertString + "\nDiese Werte sind OK:\n\n" + sensorStatusString

def sendEmail():
    # Sending email alert
    gmail_user = config["email_account"]["email"]
    gmail_password = config["email_account"]["password"]

    sent_from = gmail_user
    to = config["email_recipients"]

    sensorString = read_current_environment_and_create_alert_message()
    if sendStatusMail == True or sendStatusMail == False and sensorAlertString != '':
        body = sensorString
    
        #Setup the MIME
        message = MIMEMultipart()
        message['From'] = sent_from
        message['To'] = to[0]
        message['Subject'] = 'Status Update' if sendStatusMail else 'Sensor Alarm'  #The subject line
        #The body and the attachments for the mail
        message.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login(gmail_user, gmail_password)
            server.sendmail(sent_from, to, message.as_string())
            server.close()

            print('Email sent')
        except Exception as e: print(e)

sendEmail()