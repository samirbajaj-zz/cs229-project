"""
An implementation of a Content-Based Filtering recommender system. This program
takes three files as input: Facebook profile data in XML, metadata for the TV
shows, and a list of stopwords. Note that the metadata and Facebook profile data
should have already been run through the stemmer before being presented to this 
program. A Porter stemmer is available in porter.py.

Warning: This program takes a very long time to run.

CS 229, Stanford University, Fall 2012
Author: Samir Bajaj (http://www.samirbajaj.com)

You are free to use all or any part of this code, as long as you acknowledge this
contribution by including a reference in your work. This is a student research
project, and no warrantees of any kind are implied.
"""
from __future__ import division
import re
import sys
import math
import random
import numpy as np
import xml.etree.ElementTree as ET


def tokenize(text, word_re, splitter = None):
    if text is None or text == 'N/A': return []
    if splitter is None: return [word_re.search(w).group(0) for w in text.split() if word_re.search(w)]
    return [word_re.search(w).group(0) for w in text.split(splitter) if word_re.search(w)]

def normalize(tvShows):
    if len(tvShows) == 0: return []
    return [show.strip().lower() for show in tvShows]

def encode(text):
    if len(text) == 0: return []
    return [w.encode('utf-8') for w in text]
    
def removeStopWords(text, stopwords):
    return [w for w in text if not w in stopwords]

def filter(regex, text):
    return [w for w in text if not regex.match(w)]

def addTvShows(TV_SHOWS, idSeq, LIKES, userId, tvShows):
    showIds = set()
    for show in tvShows:
        if show not in TV_SHOWS:
            idSeq = idSeq + 1
            TV_SHOWS[show] = idSeq
            showIds.add(idSeq)
        else:
            showIds.add(TV_SHOWS[show])
    LIKES[userId] = showIds
    return idSeq

def sample(all, fraction):
    return random.sample(all, int(math.ceil(fraction * len(all))))

def createUserVector(user_words, vocabulary, vocab_size):
    result = [0] * vocab_size
    for w in user_words:
        result[ vocabulary[w] ] += 1
    return result
'''
def cosine(a, b):
    if len(a) != len(b):
        raise ValueError, "a and b must be same length"
    numerator = 0
    denoma = 0
    denomb = 0
    for i in range(len(a)):
        ai = a[i]             #only calculate once
        bi = b[i]
        numerator += ai*bi    #faster than exponent (barely)
        denoma += ai*ai
        denomb += bi*bi
    result = 1 - numerator / (math.sqrt(denoma * denomb))
    return result
'''

def cosine(u1, u2):
    norm1 = np.linalg.norm(u1)
    norm2 = np.linalg.norm(u2)
    return np.dot(u1, u2) / ( norm1 * norm2 )

def evaluate(user, LIKES, similar_users):
    shows_recommended = set()
    for sim_user in similar_users:
        shows_recommended.update(LIKES[sim_user])
    if len(shows_recommended) == 0: return (0, 0)
    # precision = fraction of shows_recommended that are liked
    precision = len(shows_recommended.intersection(LIKES[user])) / len(shows_recommended)
    # recall = fraction of liked items returned by the recommender
    recall = len(shows_recommended.intersection(LIKES[user])) / len(LIKES[user])
    return precision, recall

def computeSimilarity(USER_VECTORS, tv_watchers, test_set):
    control_set = tv_watchers - test_set
    sim_matrix = dict()
    for t in test_set:
        scores = dict() # how similar is user c to user t?
        for c in control_set:
            scores[c] = cosine(USER_VECTORS[t], USER_VECTORS[c])
        # sort desc by scores and take the top 10 similar users
        sim_matrix[t] = sorted(scores, key=scores.get, reverse=True)[:10]
    print sim_matrix
    return sim_matrix            
                                               
def parse(fbDataFile, stopwords):
    word_re = re.compile('\w+') # drop trailing non-alphanumeric chars
    TV_SHOWS = {}
    LIKES = {}
    FEATURES = {}
    showId = 0
    tree = ET.parse(fbDataFile)
    root = tree.getroot()
    for user in root.findall('user'):
        userId = None
        tvShows = None
        about = None
        movies = None
        music = None
        books = None
        activities = None
        interests = None
        try:
            userId = user.attrib['id']
            tvShows = removeStopWords( encode( normalize( tokenize(user.find('tv').text, word_re, ',') ) ), stopwords )
            movies = removeStopWords( encode( normalize( tokenize(user.find('movies').text, word_re, ',') ) ), stopwords )
            music = removeStopWords( encode( normalize( tokenize(user.find('music').text, word_re, ',') ) ), stopwords )
            books = removeStopWords( encode( normalize( tokenize(user.find('books').text, word_re, ',') ) ), stopwords )
            interests = removeStopWords( encode( normalize( tokenize(user.find('interests').text, word_re, ',') ) ), stopwords )
            if user.find('activities') is not None:
                activities = removeStopWords( encode( normalize( tokenize(user.find('activities').text, word_re, ',') ) ), stopwords )            
            about = removeStopWords( encode( normalize( tokenize(user.find('about').text, word_re)) ), stopwords )
        except UnicodeEncodeError as uerr:
            pass
        showId = addTvShows(TV_SHOWS, showId, LIKES, userId, tvShows)
        FEATURES[userId] = about
        FEATURES[userId].extend(user.find('gender').text.split())
        FEATURES[userId].extend(user.find('locale').text.split())
        FEATURES[userId].extend(movies)
        FEATURES[userId].extend(books)
        FEATURES[userId].extend(music)
        FEATURES[userId].extend(interests)
        if activities: FEATURES[userId].extend(activities)
    return TV_SHOWS, LIKES, FEATURES
        
def main(argv):
    if len(argv) > 1:
        print "Usage: Recommender.py <fbDataFile.xml>"
        sys.exit(0)
    stopwords = set( open('/Users/samir_bajaj/stanford-ml/project/stop_words.txt', 'r').read().strip().split(',') )
    TV_SHOWS, LIKES, FEATURES = parse(argv[0], stopwords)
    #
    numbers = re.compile(r'[_\d.]+') # numbers and other strange tokens made up of underscores; re.compile(r'[\d.]*\d+')
    # Parse TV_SHOWS genre text
    tv_titles = []
    tv_genre = []
    tv_text = []
    with open('/Users/samir_bajaj/stanford-ml/project/shows_all_stemmed.txt', 'r') as f:
        lines = f.readlines()
        for line in lines:
            l = line.strip().split('\t')
            tv_titles.append( removeStopWords(l[0].split(), stopwords) )
            tv_genre.append( removeStopWords(l[1].split(), stopwords) )
            tv_text.append( removeStopWords(l[2].split(), stopwords) )
    # For content-based filtering, the set of users comprises those who have watched one or more
    # shows from the list for which we have some metadata
    tv_watchers = set()
    CURATED_LIKES = dict()
    CURATED_SHOWS = dict()
    curated_show_id = 1
    # Add show titles to user profile, for all shows that the user has watched. Then iterate over
    # the list of curated shows and determine if there is a match (even remotely)--if so, add that
    # curated show to the set of shows that the user is expected to like. We do this because we'd
    # like to operate only in the domain of curated shows, i.e., ones for which we have some metadata
    # available. The user's original "likes" are in a way being mapped to these curated shows. 
    inverted = dict( (id, show) for (show, id) in TV_SHOWS.iteritems() )
    for uid in LIKES.keys():
        userCuratedShows = set()
        for showId in LIKES[uid]:
            show_title = inverted[showId].split()
            FEATURES[uid].extend(show_title)
            # search through the curated TV_SHOWS show data for a match (or close to a match)
            for idx, title in enumerate(tv_titles):
                if len(set(show_title).intersection(title)) > 0:
                    tv_watchers.add(uid)
                    key = ''.join(title)
                    if not key in CURATED_SHOWS:
                        CURATED_SHOWS[key] = curated_show_id
                        userCuratedShows.add(curated_show_id)
                        curated_show_id += 1
                    else:
                        userCuratedShows.add(CURATED_SHOWS[key])
                    # The 'sum' trick below is used to flatten out the list: sum(l, [])
                    # will flatten a list of lists
                    FEATURES[uid].extend([w for w in sum([genre.split(',') for genre in tv_genre[idx]], []) if len(w) > 0])
        FEATURES[uid] = filter(numbers, FEATURES[uid])
        CURATED_LIKES[uid] = userCuratedShows

    # So we now have the FEATURES map that contains all the stemmed words from the following sources:
    #     (i) The 'about' field in a user's profile
    #    (ii) The titles of the TV_SHOWS shows liked by the user
    #   (iii) The genre keywords of the TV_SHOWS shows liked (or similar to those liked) by the user
    #
    all_features = set([])
    for uid in FEATURES.keys(): all_features.update(FEATURES[uid])
    all_words = sorted(list(all_features))
    vocabulary = dict()
    for idx, word in enumerate(all_words):
        vocabulary[word] = idx

    USER_VECTORS = dict()
    for uid in FEATURES.keys():
        USER_VECTORS[uid] = createUserVector(FEATURES[uid], vocabulary, len(all_words))
    test_set = set(sample(tv_watchers, 0.3))
    # For each test user, compute the top N=10 users similar to him
    sim_matrix = computeSimilarity(USER_VECTORS, tv_watchers, test_set)
    aggr_precision = 0.0
    aggr_recall = 0.0
    for u in sim_matrix.keys():
        (precision, recall) = evaluate(u, CURATED_LIKES, sim_matrix[u])
        print precision, recall
        aggr_precision += precision
        aggr_recall += recall
    aggr_size = len(sim_matrix.keys())
    P = aggr_precision/aggr_size
    R = aggr_recall/aggr_size
    print P, R, (2 * P * R)/(P + R)


if __name__ == '__main__':
    main(sys.argv[1:])
