from gensim.parsing.preprocessing import remove_stopwords, strip_punctuation, strip_numeric, strip_non_alphanum, strip_multiple_whitespaces, strip_short
from nltk import word_tokenize
import nltk
import re
from nltk.stem import WordNetLemmatizer

# Python3 implementation of above approach
from math import floor
 
# Function to calculate the
# Jaro Similarity of two strings
def jaro_distance(s1, s2):
 
    # If the strings are equal
    if (s1 == s2):
        return 1.0
 
    # Length of two strings
    len1 = len(s1)
    len2 = len(s2)
 
    if (len1 == 0 or len2 == 0):
        return 0.0
 
    # Maximum distance upto which matching
    # is allowed
    max_dist = (max(len(s1), len(s2)) // 2 ) - 1
 
    # Count of matches
    match = 0
 
    # Hash for matches
    hash_s1 = [0] * len(s1)
    hash_s2 = [0] * len(s2)
 
    # Traverse through the first string
    for i in range(len1):
 
        # Check if there is any matches
        for j in range( max(0, i - max_dist),
                    min(len2, i + max_dist + 1)):
             
            # If there is a match
            if (s1[i] == s2[j] and hash_s2[j] == 0):
                hash_s1[i] = 1
                hash_s2[j] = 1
                match += 1
                break
         
    # If there is no match
    if (match == 0):
        return 0.0
 
    # Number of transpositions
    t = 0
 
    point = 0
 
    # Count number of occurrences
    # where two characters match but
    # there is a third matched character
    # in between the indices
    for i in range(len1):
        if (hash_s1[i]):
 
            # Find the next matched character
            # in second string
            while (hash_s2[point] == 0):
                point += 1
 
            if (s1[i] != s2[point]):
                point += 1
                t += 1
            else :
                point += 1
                 
        t /= 2
 
    # Return the Jaro Similarity
    return ((match / len1 + match / len2 +
            (match - t) / match ) / 3.0)

# Jaro Winkler Similarity
def jaro_Winkler(s1, s2):
 
    jaro_dist = jaro_distance(s1, s2)
 
    # If the jaro Similarity is above a threshold
    if (jaro_dist > 0.7):
 
        # Find the length of common prefix
        prefix = 0
 
        for i in range(min(len(s1), len(s2))):
         
            # If the characters match
            if (s1[i] == s2[i]):
                prefix += 1
 
            # Else break
            else:
                break
 
        # Maximum of 4 characters are allowed in prefix
        prefix = min(4, prefix)

        # Calculate jaro winkler Similarity
        jaro_dist += 0.1 * prefix * (1 - jaro_dist)

    return jaro_dist

def get_similarity(mention_token, kb_tokens, tag):
  highest_sim = 0
  if tag != 'NOUN':
    return 0
  if mention_token in kb_tokens:
    return 1.0
  for token in kb_tokens:
    highest_sim = max(highest_sim, jaro_distance(token, mention_token))
  return highest_sim

def process_mention(mention, threshold, kb_tokens):
  tokens = word_tokenize(mention)
  
  if len(tokens) == 1:
    return mention
  else:
    tagged_tokens = nltk.pos_tag(tokens, tagset='universal')
    new_mention = ''
    for tagged_token in tagged_tokens:
      if get_similarity(tagged_token[0], kb_tokens, tagged_token[1]) >= threshold:
        new_mention += tagged_token[0] + ' '
    if new_mention == '':
      return mention
    return new_mention[:-1]

def get_mention_similarity_score_for_pair(mention, entity, kb_tokens, processed_mention, threshold=0.91):
    copy_mention = mention 
    
    similarity1 = jaro_distance(mention, entity) # Score before processing
    highest_sim = similarity1
    mention = processed_mention
    if mention != copy_mention: 
        similarity2 = jaro_distance(mention, entity) # Score after processing
        highest_sim = max(highest_sim, similarity2)

    tokens = word_tokenize(copy_mention) # Compute the score for the swapped version of the INITIAL mention in case it has two tokens
    if len(tokens) == 2:
        new_mention = tokens[1] + ' ' + tokens[0]
        similarity3 = jaro_distance(new_mention, entity)
        highest_sim = max(highest_sim, similarity3)
    tokens = word_tokenize(mention)
    if len(tokens) == 2: # Compute the score for the swapped version of the PROCESSED mention in case it has two tokens
        new_mention = tokens[1] + ' ' + tokens[0]
        similarity4 = jaro_distance(new_mention, entity)
        highest_sim = max(highest_sim, similarity4)

    return highest_sim

def get_linked_products(mention, kb_data, kb_tokens):
    mention = clean_mention(mention)
    entities_similarities = []
    
    if mention in kb_data:
        return kb_data[mention][:10]

    processed_mention = process_mention(mention, 0.91, kb_tokens) # Process the mention, i.e. remove any tokens which are not similar enough to the ones we have in KB

    scores = {}
    for concept in kb_data:
        scores[concept] = []
        current_score = get_mention_similarity_score_for_pair(mention=mention, entity=concept, kb_tokens=kb_tokens, processed_mention=processed_mention)
        # current_score = jaro_distance(mention, concept)
        max_score = current_score
        pos = 0
        for entity in kb_data[concept]:
            current_score = get_mention_similarity_score_for_pair(mention=mention, entity=entity['cleaned_full_name'], kb_tokens=kb_tokens, processed_mention=processed_mention)
            # current_score = jaro_distance(mention, entity['cleaned_full_name'])
            max_score = max(max_score, current_score)
            scores[concept].append((pos, current_score))
            pos += 1
            if max_score == 1.0:
                break
        entities_similarities.append((concept, max_score))

    entities_similarities = sorted(entities_similarities, key=lambda tuple: tuple[1], reverse=True)
    linked_product_concept = entities_similarities[0]
    most_similar_products_from_concept = sorted(scores[linked_product_concept[0]], key=lambda tuple: tuple[1], reverse=True)
    products = []
    for i in range(min(len(most_similar_products_from_concept), 3)):
        tuple = most_similar_products_from_concept[i]
        pos = tuple[0]
        score = tuple[1]
        products.append(kb_data[linked_product_concept[0]][pos])
        # print(kb_data[linked_product_concept[0]][pos]['cleaned_full_name'])
        # print(get_mention_similarity_score_for_pair(mention, kb_data[linked_product_concept[0]][pos]['cleaned_full_name'], kb_tokens, processed_mention))
        # print(score)
    return products
#   for item in entities_similarities:
#       if item[0] not in concepts:
#           concepts[item[0]] = {
#                                 'nr' : 0,
#                                 'sum_scores' : 0
#                                }
#       concepts[item[0]]['nr'] += 1
#       concepts[item[0]]['sum_scores'] += 1
#   for item in concepts:
#       if concepts[item]['sum_scores'] / concepts[item]['nr'] > max_score:
#           max_score = concepts[item]['sum_scores'] / concepts[item]['nr'] 
#           max_concept = item
#   print(max_concept, max_score)
#   print(entities_similarities)
#   print(len(kb_data[max_concept]))

    # print('tamarind' in kb_tokens)
    # print(process_mention('east end tamarind sauce', 0.91, kb_tokens))
    # print(len(kb_tokens))
    # print(jaro_distance('tamarind', process_mention('east end tamarind sauce', 0.91, kb_tokens)))
    # print(get_mention_similarity_score_for_pair(mention='sour cream', entity='sour cream creme fraiche', kb_tokens=kb_tokens))




def clean_mention(mention):

  wnl = WordNetLemmatizer()
  copy_mention = mention
  mention = remove_stopwords(mention)
  mention = mention.lower()
  mention = strip_numeric(mention)
  mention = strip_punctuation(mention)
  mention = strip_non_alphanum(mention)
  mention = strip_multiple_whitespaces(mention)
  mention = strip_short(mention, 2)

  mention = re.sub(r'\(.*oz.\)|(®)|\bpint(s)*\b|\bkg\b|\bmg\b|\btesco\b|\bpack\b|\bportion(s)*\b|tast|\bsprig\b|\binch\b|\bpurpose\b|\bflmy\b|\btaste\b|boneless|skinless|chunks|fresh|\blarge\b|cook drain|green|frozen|\bground\b|tablespoon|teaspoon|\bcup\b','',mention).strip()

  tokens = word_tokenize(mention)
  tags = nltk.pos_tag(tokens, tagset='universal')
  tokens_sentence = [wnl.lemmatize(tag[0]) if tag[1] == 'NOUN' else tag[0] for tag in tags]
  sentence = ' '.join(token for token in tokens_sentence)
  if sentence:
    return sentence
  else:
    return copy_mention.lower().strip()