import codecs
import io
import json
import os
import pickle
import string
import time
from datetime import datetime

import flask
import numpy as np
import psycopg2
import pytz
from flask import Flask, jsonify, request
from gensim.models import Word2Vec

tz = pytz.timezone('Europe/London')

import nltk

from utils import (clean_mention, get_linked_products, jaro_distance,
                   jaro_Winkler)

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('universal_tagset')
nltk.download('wordnet')

app = Flask(__name__)

model = Word2Vec.load("word2vec.model")

NUMBER_OF_SECONDS = 86400 # Seconds in a day / 24hrs

last_time_loaded_tesco_kb = None

connection = psycopg2.connect(user="doadmin",
                              password="ovQrVQuXgQsDlp2i",
                              host="app-af20c605-75f8-45be-9aa4-92d508f1d985-do-user-10787135-0.b.db.ondigitalocean.com",
                              port="25060",
                              database="defaultdb")
cursor = connection.cursor()

def update_tesco_data():
    global tesco_kb_data, tesco_protected_tokens, last_time_loaded_tesco_kb
    insert_query = """SELECT protected_tokens, products_data
                      FROM supermarkets_data_tescodata;"""
    cursor.execute(insert_query)
    connection.commit()
    record = cursor.fetchone()
    if record:
        global tesco_kb_data, tesco_protected_tokens
        tesco_kb_data = record[1]
        tesco_protected_tokens = set(record[0])
        last_time_loaded_tesco_kb = datetime.now(tz)

@app.route('/api/food/', methods=['GET'])
def api_id():
    # print(last_time_loaded_tesco_kb)
    global last_time_loaded_tesco_kb
    if last_time_loaded_tesco_kb and (datetime.now(tz) - last_time_loaded_tesco_kb).total_seconds() >= NUMBER_OF_SECONDS:
        update_tesco_data()

    # Check if an ID was provided as part of the URL.
    # If ID is provided, assign it to a variable.
    # If no item is provided, display an error in the browser.
    if 'item' in request.args and request.args['item']:
        food_item = request.args['item']
    else:
        return "Error: No food item field provided. Please specify a food item (e.g. ?item=tomato)."

    # Create an empty list for our results
    results = get_linked_products(food_item, tesco_kb_data, tesco_protected_tokens)
    if results:
        # Use the jsonify function from Flask to convert our list of
        # Python dictionaries to the JSON format.
        return jsonify(results)
    return jsonify([])
    
@app.route('/', methods=['GET'])
def index():
    return 'Food price comparator Interface'


if __name__ == '__main__':
    update_tesco_data()
    app.run(debug=True, host='0.0.0.0')
