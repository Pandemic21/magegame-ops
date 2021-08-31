from flask import Flask, render_template, jsonify, request
from flask import url_for
from subprocess import check_output
import git
import logging
import os
import random
import json


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
Fix the update (method not allowed)
'''


# Global variables
OPS_CONSOLE_VERSION = "0.0.1"
local_files = "/opt/magegame-updater/"
index = local_files + "index.html"
static_folder_root = "./static"
# End global variables

# Flask config
app = Flask(__name__,
            static_folder=static_folder_root,
            template_folder='./templates')
# End Flask config


######################
# Navagatable Routes #
######################


# Route: /

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
            updateMainBranch()

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


# Route: /home #

@app.route('/home', methods=['GET'])
def home():
    return render_template('home.html')


# Route: /update

@app.route('/update', methods=['GET', 'POST'])
def update():
    # if they clicked the "Main" button, update the "/opt/magegame" branch
    if request.method == 'POST':
        if 'Main' in d:
            updateMainBranch()

    return render_template('update.html')


# Route: /console

@app.route('/console', methods=['GET'])
def console():
    return render_template('console.html')


# Route: /services

@app.route('/services', methods=['GET'])
def services():
    return render_template('services.html')


##############
# API Routes #
##############

# Route: /api/version/magegame

@app.route('/api/version/magegame', methods=["GET"])
def apiGetMageGameVersion():
    program = request.args.get('p')
    f = open("../magegame/package.json", "r")
    return json.load(f)['version']


# Route: /api/version/opsconsole

@app.route('/api/version/opsconsole', methods=["GET"])
def apiGetOpsConsoleVersion():
    return OPS_CONSOLE_VERSION


# Route: /api/serviceCheck

@app.route('/api/serviceCheck', methods=["GET"])
def apiServiceCheck():
    service = request.args.get('s')
    stat = -999

    # magegame.service
    if service == "magegame.service":
        stat = os.system('systemctl status magegame.service')

    # magegame-ops.service
    elif service == "magegame-ops.service":
        stat = os.system('systemctl status magegame-ops.service')

    # Parse what "stat" means
    if stat == 0:
        return '<span class="text-success">Running</span>'
    elif stat == -999:
        return "Service not found"
    else:
        return '<span class="text-danger">NOT running</span>'


# Route: /api/serviceDetails

@app.route('/api/serviceDetails',  methods=["GET"])
def apiServiceDetails():
    service = request.args.get('s')
    stat = -999

    # magegame.service
    if service == "magegame.service":
        result = check_output(['systemctl', 'status', 'magegame.service']).decode("utf-8")

    # magegame-ops.service
    elif service == "magegame-ops.service":
        result = check_output(['systemctl', 'status', 'magegame-ops.service']).decode("utf-8")

    return str(result)


# Route: /api/serviceUpdate

@app.route('/api/serviceUpdate', methods=["GET"])
def apiServiceUpdate():
    service = request.args.get('s')

    # magegame.service
    if service == "magegame.service":
        updateMainBranch()


# Route: /api/serviceRestart

@app.route('/api/serviceRestart', methods=["GET"])
def apiServiceRestart():
    service = request.args.get('s')
    result = ''

    # magegame.service
    if service == "magegame.service":
        os.system('sudo systemctl restart magegame-ops.service')
        result = check_output(['systemctl', 'status', 'magegame.service']).decode("utf-8")

    # magegame-ops.service
    elif service == "magegame-ops.service":
        os.system('sudo systemctl restart magegame-ops.service')
        result = check_output(['systemctl', 'status', 'magegame-ops.service']).decode("utf-8")

    return str(result)





##########################
# Local Helper Functions #
##########################
def updateMainBranch():
    logger.info("Request to update main branch...")
    logger.info("Stopping magegame.service...")
    os.system('sudo systemctl stop magegame.service')
    logger.info("Stopped.")
    logger.info("Pulling new version...")
    os.system('git -C /opt/magegame/ fetch --all')
    os.system('git -C /opt/magegame/ reset --hard main')
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



if __name__ == '__main__':
    app._static_folder = static_folder_root
    app.run(host='0.0.0.0', port=5001)
