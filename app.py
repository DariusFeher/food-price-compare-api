import flask
import io
import string
import time
import os
import numpy as np
import tensorflow as tf
from PIL import Image
from flask import Flask, jsonify, request

from gensim.models import Word2Vec
from gensim.parsing.preprocessing import remove_stopwords, strip_punctuation, strip_numeric, strip_non_alphanum, strip_multiple_whitespaces, strip_short
from nltk import word_tokenize
import nltk
import re
from nltk.stem import WordNetLemmatizer

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('universal_tagset')

def clean_mention(sentence):
  wnl = WordNetLemmatizer()
  copy_sentence = sentence
  sentence = remove_stopwords(sentence)
  sentence = sentence.lower()
  sentence = strip_numeric(sentence)
  sentence = strip_punctuation(sentence)
  sentence = strip_non_alphanum(sentence)
  sentence = strip_multiple_whitespaces(sentence)
  sentence = strip_short(sentence,2)

  sentence = re.sub(r'\(.*oz.\)|(®)|pint(s)*|tesco|pack|portion(s)*|tast|sprig|inch|purpose|flmy|taste|boneless|skinless|chunks|fresh|large|cook drain|green|frozen|ground|tablespoon|teaspoon|cup','',sentence).strip()

  tokens = word_tokenize(sentence)
  tags = nltk.pos_tag(tokens, tagset='universal')
  tokens_sentence = [wnl.lemmatize(tag[0]) if tag[1] == 'NOUN' else tag[0] for tag in tags]
  sentence = ' '.join(token for token in tokens_sentence)
  return sentence

model = Word2Vec.load("word2vec.model")

def get_vector_representation(foodname):
  result = None
  foodname = clean_mention(foodname)
  if ' ' in foodname:
    ngram = foodname.lower().replace(' ', '_')
    if ngram in model.wv:
      result = model.wv[ngram]
      #print('BRANCH 1:' + str(result.shape))
      return result
 
  vector_list = []
  for word in foodname.split(' '):
    if word in model.wv:
      vector_list.append(model.wv[word])
  if len(vector_list) < 1:
    result = None
  else:
    result = np.mean(vector_list, axis=0)
  #print('BRANCH 2:' + str(result.shape))
  return result
 

def predict_most_similar(food):
    food_avg_vector = get_vector_representation(food)
    if food_avg_vector is not None:
        return model.wv.similar_by_vector(food_avg_vector)
    return None


app = Flask(__name__)

@app.route('/api/food/', methods=['GET'])
def api_id():
    # Check if an ID was provided as part of the URL.
    # If ID is provided, assign it to a variable.
    # If no ID is provided, display an error in the browser.
    if 'item' in request.args:
        food_item = request.args['item']
    else:
        return "Error: No food item field provided. Please specify a food item (e.g. ?item=tomato)."

    # Create an empty list for our results
    results = predict_most_similar(food_item)
    if results:
        # Use the jsonify function from Flask to convert our list of
        # Python dictionaries to the JSON format.
        return jsonify(results)
    return jsonify([])

@app.route('/', methods=['GET'])
def index():
    return 'Machine Learning Inference'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')