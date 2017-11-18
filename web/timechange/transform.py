"""Copyright 2017
Steven Sheffey <stevensheffey4@gmail.com>,
John Ford,
Eyasu Asrat,
Jordan Flowers,
Joseph Volmer,
Luke Stanley,
Serenah Smith, and
Chandu Budati

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

# For navigating filesystems
import os
from os import path
# For deleting directories
import shutil
# For creating images from numpy arrays
from PIL import Image
# For reading csv files
import pandas
import numpy as np
from scipy import signal


def convert_all_csv(project_path, method, chunk_size, fft_size, columns):
    """
    Iterates over the training files set and generates corresponding images
    using the feature extraction method
    Keyword arguments:
    project path -- path to project data (kept as a global in flask)
    method -- Method used by extract_features to generate image data. Default: fft
    chunk_size -- number of timesteps to include in each fft
    fft_size -- size of the fft
    columns -- comma separated string of columns to use
    """

    # Columns to read from the csv
    columns = columns.split(",")

    # Default to reading all columns if this fails
    if columns == [""]:
        columns = None

    # Clear subfolders in image folder without deleting images folder
    # This is to make sure old images don't stick around
    # In case a file has been removed
    for label in os.scandir(path.join(project_path, "images")):
        # Delete the folder
        try:
            shutil.rmtree(label.path)
        except FileNotFoundError as _:
            # Do nothing
            pass

    # Get length of longest csv file
    max_length = -1

    # Iterate over labels
    for label in os.scandir(path.join(project_path, "csv")):

        # Iterate over a label's csv files
        for csv_file in os.scandir(label.path):
            with open(csv_file.path, 'r') as csv_file_handle:
                # Get number of lines in file and keep track of longest file
                max_length = max(max_length, len(csv_file_handle.readlines()) - 1)

    # Generate new images
    # Iterate over labels
    for label in os.scandir(path.join(project_path, "csv")):
        # Make a folder for the label
        os.mkdir(path.join(project_path, "images", label.name))

        # Iterate over a label's csv files
        for csv_file in os.scandir(label.path):
            # Read the csv into a numpy array
            data = pandas.read_csv(csv_file.path, usecols=columns).as_matrix().T

            # Pad the csv
            data = np.pad(data, ((0, 0), (0, max_length - data.shape[1])), 'constant', constant_values=0.0)

            # Extract features from the numpy array
            # Uses same variable name since data is not needed after feature extraction
            data = extract(data, method, chunk_size=chunk_size, fft_size=fft_size)

            # TODO: normalize and imageize here
            # TODO: Don't imagize at all
            # Generate an image from the resulting feature representation
            img = Image.fromarray((data * 255).astype(np.uint8), "RGB")

            # Save the image to the desired file path
            # project/csv/example/1.csv becomes
            # project/images/example/1.png
            img.save(
                path.join(project_path, "images", label.name, "{}.png".format(path.splitext(csv_file.name)[0])))


def extract(time_series, method, **kwargs):
    """Extracts features from a time series or array of time series and outputs an image
    Keyword arguments:
    time_series -- A numpy array or array of numpy arrays representing the time series data
    method -- the type of feature extraction to use
    chunk_size -- Used for some feature extraction methods. Pads or truncates data
    """
    # Switches on method
    if method == "fft":
        return simple_fourier(time_series, **kwargs)
    elif method == "spectrogram":
        return spectrogram(time_series)
    elif method == "nothing":
        return nothing(time_series)
    else:
        raise Exception("Invalid feature extraction method")


# Possible enhancements
# TODO: separate real and imaginary components so as not to lose data
# TODO: split time series into chunks
# TODO: ignoring values with little information
# TODO: version with axes
def simple_fourier(time_series, chunk_size=64, fft_size=128):
    """
    Performs a basic fourier transform across the entire time series. The imaginary results are normalized.
    Keyword arguments:
    time_series -- The time series analyse as a 2d numpy array
    chunk_size -- The size value to be passed to numpy's FFT. Values higher than the data size will pad zeroes.
                 Values lower than the data size will remove elements.
                 With FFT, it is recommended to use powers of 2 here
    """
    # Store the number of time series streams
    num_time_series = time_series.shape[0]

    # Pad the data to chunk size
    pad_length = chunk_size - (time_series.shape[1] % chunk_size)
    time_series = np.pad(time_series, ((0, 0), (0, pad_length)), 'constant', constant_values=0)

    # Reshape the data to chunks of suitable size
    time_series = time_series.reshape(int(np.product(time_series.shape) / chunk_size), chunk_size)

    # Perform FFT on the resulting data
    # Store in the time_series variable since that data is no longer needed
    # Normalize the real and complex features
    time_series = np.abs(np.fft.rfft(time_series, fft_size))

    # Store the chunked shape
    chunked_shape = time_series.shape

    # Reshape it back to num_waves, * for normalization
    time_series = time_series.reshape((num_time_series, np.product(time_series.shape) // num_time_series))

    # Normalize against maximum value per row to get all values between 0 and 1
    # Extract max values and replace 0s to avoid divide by 0 issue
    max_values = np.max(time_series, axis=1)
    np.place(max_values, max_values == 0, 1)

    # Normalize the time series data by row
    time_series = (time_series.T / max_values).T

    # Reshape the time series back to its chunked shape
    time_series = time_series.reshape(chunked_shape)

    # TODO: configure whether shuffled or stacked
    # Shape of this array is W, H, 3
    return np.stack((time_series, time_series, time_series), axis=2)


def nothing(time_series):
    """
    Normalizes the data to positive values and returns it as a 2d array
    Parameters:
        time_series -- The data to transform
    """
    # Bring all values up to positive
    time_series -= np.min(time_series, axis=1).reshape(time_series.shape[0], 1)

    # Normalize all rows per row
    # Get normalization values
    max_values = np.max(time_series, axis=1).reshape(time_series.shape[0], 1)

    # Fix divby0 errors
    max_values[max_values == 0] = 1

    # Return the array normalized
    return np.stack([time_series / max_values] * 3, axis=2)


def spectrogram(time_series):
    """Performs a spectrogram
    Parameters:
    time_series -- The time series to analyse as a 2d array.
    """
    # Generate the spectrogram
    f,t,Sxx = signal.spectrogram(time_series.flatten())

    # Return the data
    return np.stack([Sxx] * 3, axis=2)
