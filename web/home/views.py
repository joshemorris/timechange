import sys
import os
import json
import shutil
import stat
import os.path as path
from web import settings
from web import app
from flask import render_template, redirect, flash, url_for, request, jsonify, send_from_directory
from werkzeug import secure_filename

ALLOWED_EXTENSIONS = set(['csv', 'xls', 'xlsx'])
PROJECT_PATH = path.join(path.dirname(path.abspath(__file__)), '../default/')
# app.config['PROJECT_PATH'] = PROJECT_PATH

# cache = Cache()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_default_dir():
    # create default dir
    os.mkdir(PROJECT_PATH)
    # under default create csv dir
    os.mkdir(os.path.join(PROJECT_PATH, 'csv/'))
    # under default create images dir
    os.mkdir(os.path.join(PROJECT_PATH, 'images/'))
    # under default create models dir
    os.mkdir(os.path.join(PROJECT_PATH, 'models/'))
    # under default create files dir
    os.mkdir(os.path.join(PROJECT_PATH, 'files/'))

def remove_default_dir():
    shutil.rmtree(PROJECT_PATH)
    if os.path.isdir(PROJECT_PATH):
        print("rmdir")
        os.rmdir(PROJECT_PATH)


def remove_label_dirs():
    shutil.rmtree(os.path.join(PROJECT_PATH, 'csv/'))
    os.mkdir(os.path.join(PROJECT_PATH, 'csv/'))

def create_directory(post_data):
    # remove existing label folders to add new set
    for index in range(len(post_data)):
        if os.path.isdir(os.path.join(PROJECT_PATH, 'csv/' + post_data[index]['label'])):
            shutil.rmtree(os.path.join(PROJECT_PATH, 'csv/' + post_data[index]['label']))

    # add file label folders and copy files
    # to respective folder
    for num in range(len(post_data)):
        #if label-name folder exists in label folder
        if (os.path.isdir(os.path.join(PROJECT_PATH, 'csv/' + post_data[num]['label']))) == False:
            os.mkdir(os.path.join(PROJECT_PATH, 'csv/' + post_data[num]['label']))
        shutil.copy(os.path.join(PROJECT_PATH, 'files/' + post_data[num]['file_name']), os.path.join(PROJECT_PATH, 'csv/' + post_data[num]['label']))


@app.route('/')
@app.route('/home')
def home():
    # Initialize function from __init__.py
    return render_template("home.html")

# helper function to remove __pycache__ directories in project
def remove_pycache():
    for root, dirs, files in os.walk(os.path.join(PROJECT_PATH, '../')):
        for directory in dirs:
            exts = ('__pycache__')
            if directory == exts:
                shutil.rmtree(os.path.join(root, directory))

@app.route('/initProject', methods=['POST'])
def initProject():
    # remove __pycache__ directories in project
    remove_pycache()

    # if default dir exists
    # delete and create
    if os.path.isdir(PROJECT_PATH):
        remove_default_dir();
        create_default_dir();
    else:
        create_default_dir();

    return (''), 204

@app.route('/loadFiles')
def loadFiles():
    file_names = []
    return render_template("loadFiles.html", file_names=file_names, slideUp=True)

@app.route('/transformData')
def transformData():
    return render_template("transformData.html")

@app.route('/displayImage/<directory>/<filename>')
def displayImage(filename, directory):
    return send_from_directory(os.path.join(PROJECT_PATH, "images/" + directory), filename)
    print(os.path.join(PROJECT_PATH, "images/" + directory + "/" + filename))

@app.route('/FFTPreview')
def FFTPreview():
    image_list = []     # list of lists used to store dir name and image file of each file
    image = []          # tmp list
    dirs = []           # used to store directories
    image_names = []    # used to store image names

    # grab the dir names to iterate through
    image_dirs = os.listdir(os.path.join(PROJECT_PATH, "images"))

    # iterate through each directory
    for directory in image_dirs:
        # grab the file names from target dir
        image_files = os.listdir(os.path.join(PROJECT_PATH, "images/" + directory))
        # create a list of lists, each inner list contains dir name and image_name
        for image_file in image_files:
            image.append(directory)
            image.append(image_file)
            image_list.append(image)
            image = []

    # fill dirs and image_names
    for i in image_list:
        # if the dir index exists, skip
        # dirs list should only contain 1 dir value per dir
        try:
            x = dirs.index(i[0])
        except:
            dirs.append(i[0])
        image_names.append(i[1])

    if len(image_names) == 0:
        return (''), 204
    return render_template("FFTPreview.html", image_names=image_names, dirs=dirs)

@app.route('/configure')
def configure():
    return render_template("configure.html")

@app.route('/results')
def results():
    return render_template("results.html")

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

# TODO: ability to upload a set of files more than once
@app.route('/upload', methods=['POST'])
def upload():
    remove_default_dir();
    create_default_dir();
    file_names = []
    target = path.join(PROJECT_PATH, "files/")

    #input_files from html form and save locally
    for file in request.files.getlist("file"):
        # if an empty form, return
        if file.filename == '':
            return render_template('loadFiles.html', file_names=file_names, flag='fail', message="No files were added")
        file_names.append(secure_filename(file.filename))
        filename = secure_filename(file.filename)
        file.save(os.path.join(target, filename))
        file.close()

    return render_template('loadFiles.html', file_names=file_names, flag='success', message="Success uploading files")

@app.route('/getjson', methods=['POST'])
def getjson():
    # path to files
    target = path.join(PROJECT_PATH, "csv/")

    post_data = request.get_json()

    file_names=[]
    try:
        create_directory(post_data)
    except:
        return render_template('loadFiles.html', file_names=file_names, flag='fail', message="There was a problem adding the labels to the project")

    return render_template('upload.html', file_names=file_names, flag='success', message="Success adding labels")
