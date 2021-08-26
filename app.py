from flask import Flask, render_template, jsonify, request
import test
import git
import logging
import os
import random

### setup logging...
# create logger with 'spam_application'
logger = logging.getLogger('magegame-ops')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('magegame-ops.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)
### end logging

# TODO:
'''
Add a button to reload daemons
Add a button to launch the game in a new window
Make everything ajax calls
'''


# Global variables
app = Flask(__name__)
local_files = "/opt/magegame-updater/"
index = local_files + "index.html"
counter = 0
# End global variables

@app.route('/api/service',  methods=["GET"])
def mageGameService():
    service = request.args.get('s')
    if service == "magegame.service":
        tmpFile = str(random.randint(0,99))
        os.system('systemctl status magegame.service > ' + tmpFile)
        f = open(tmpFile, "r")
        magegamelogs = f.read()
        os.remove(tmpFile)
        return magegamelogs
    elif service == "magegame-ops.service":
        return "Client sent: magegame-ops.service"
    else:
        return "not a valid service: "

@app.route('/', methods=['POST', 'GET'])
def index():
    # POST request
    if request.method == 'POST':
        logger.info("POST request...")
        logger.info(request.form)
        # get the button they pressed
        d = request.form.getlist('action')

        # Button: Main
        if 'Main' in d:
            logger.info("Request to update main branch...")
            logger.info("Stopping magegame.service...")
            os.system('sudo systemctl stop magegame.service')
            logger.info("Stopped.")
            logger.info("Pulling new version...")
            os.system('git -C /opt/magegame/ fetch --all')
            os.system('git -C /opt/magegame/ reset --hard orgin/main')
            os.system('git -C /opt/magegame/ pull')
            logger.info("Pulled.")
            logger.info("Running npm install...")
            os.system('rm -r "/opt/magegame/node_modules"')
            os.system('npm --prefix /opt/magegame/ i /opt/magegame/')
            logger.info("npm modules installed.")
            logger.info("Restarting magegame.service...")
            os.system('sudo systemctl start magegame.service')
            logger.info("Restarted.")
            logger.info("Updated.")

        # Button: Restart service
        elif 'magegame.service' in d:
            logger.info("Request to restart service...")
            os.system('sudo systemctl restart magegame.service')
            logger.info("Complete.")

        elif 'magegame-updater.service' in d:
            logger.info("Request to restart magegame-updater.service...")
            os.system('sudo systemctl restart magegame-updater.service')
            logger.info("Complete.")

        else:
            logger.info("No button found")

    # GET request
    elif request.method == 'GET':
        logger.info("GET request...")

    # Unsupported HTTP method
    else:
        logger.info("Unsupported method")

    # Get logs data
    os.system('systemctl status magegame.service > temp')
    f = open("temp", "r")
    magegamelogs = f.read()
    os.system('systemctl status magegame-updater.service > temp')
    f = open("temp", "r")
    magegameupdaterlogs = f.read()

    # Get version
    try:
        f = open("/opt/magegame/version", "r")
        magegameversion = f.read()
    except:
        logger.error("Error reading version")
        magegameversion = "?"

    # Return them to index.html
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
