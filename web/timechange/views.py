from web import settings
from web import app
from flask import render_template, redirect, flash, url_for, request
from flask_restful import reqparse
from .model import *
from .transform import *
from .train import *

PROJECT_PATH = path.join(path.dirname(path.abspath(__file__)), '../default/')
app.config['PROJECT_PATH'] = PROJECT_PATH

@app.route('/transform_data_timechange', methods=['POST'])
def transform_data_timechange():
    """
    Iterates over the training files set and generates corresponding images
    using the feature extraction method

    Keyword arguments:
    project path -- path to project data (kept as a global in flask)
    method       -- Method used by extract_features to generate image data. Default: fft
    chunk_size   -- number of timesteps to include in each fft
    fft_size     -- size of the fft
    columns      -- comma separated string of columns to use
    """

    try:
        parser = reqparse.RequestParser()
        parser.add_argument('options', type=str, required=True)
        parser.add_argument('chunk_size', type=int, required=True)
        parser.add_argument('fft_size', type=int, required=True)
        parser.add_argument('columns', required=True)
        args = parser.parse_args()
    except:
        return render_template("transformData.html", flag='fail', message="A problem occured when gathering form input.")

    try:
        convert_all_csv(PROJECT_PATH, args['options'], args['fft_size'], args['chunk_size'], args['columns'])
        return render_template("transformData.html", flag='success', message="Success")
    except:
        return render_template("transformData.html", flag='fail', message="Something went wrong when converting csv files")

# remove any models that may already exist
def remove_models():
    model_files = os.listdir(os.path.join(PROJECT_PATH, "models/"))
    if len(model_files) > 0:
        for item in model_files:
            if item.endswith(".h5"):
                os.remove(os.path.join(PROJECT_PATH, "models/" + item))


@app.route('/configure_timechange', methods=['POST', 'GET'])
def configure_timechange():
    """
    Generates a compiled keras model for use in timechange training
    Parameters:
    project_path -- path to a timechange project
    config -- dict containing configuration setting (model_type, num_block, num_filters, learning_rate)
    """
    # remove existing models
    remove_models();

    try:
        # grab form input from configure.html
        pars = reqparse.RequestParser(bundle_errors=True)
        pars.add_argument('model_type', required=True)
        pars.add_argument('num_block', type=int, required=True)
        pars.add_argument('num_filters', type=str, required=True)
        pars.add_argument('learning_rate', type=float, required=True)
        args = pars.parse_args()
    except:
        return render_template("configure.html", flag='fail', message="A problem occured when gathering form input. ")

    # Call build_model
    try:
        build_model(PROJECT_PATH, args)
        return render_template("configure.html", flag='success', message="Success")
    except:
        return render_template("configure.html", flag='fail', message="Something went wrong when building the model.")

@app.route('/train_timechange', methods=['POST'])
def train_timechange():
    """
    Generates a compiled keras model for use in timechange training
    Parameters:
    project_path -- path to a timechange project
    config -- dict containing configuration setting (model_type, num_block, num_filters, learning_rate)
    """
    ret = ''
    try:
        ret = train(PROJECT_PATH)
    except:
        return render_template("results.html", ret=ret, flag='fail', message="Training failed")

    return render_template("results.html", ret=ret, flag='success', message="Training succeeded")












# space
