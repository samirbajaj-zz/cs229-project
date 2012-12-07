"""
An implementation of a Collaborative Filtering recommender system. This program
takes two files as input: Facebook profile data in XML, and a list of stopwords.
Both user-based as well as item-based methods are implemented.

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
import xml.etree.ElementTree as ET


def tokenize(tvShows, splitter = None):
    if tvShows is None or tvShows == 'N/A': return []
    if splitter is None: return tvShows.split()
    return tvShows.split(splitter)

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

def addItems(LIKES):
    LIKED_BY = {}
    for u in LIKES.keys():
        for show in LIKES[u]:
            if not show in LIKED_BY: LIKED_BY[show] = set([])
            LIKED_BY[show].add(u)
    return LIKED_BY

def sample(all, fraction):
    return random.sample(all, int(math.ceil(fraction * len(all))))

def cosine(LIKES, u1, u2):
    common = LIKES[u1].intersection(LIKES[u2])
    try:
        return len(common) / ( math.sqrt(len(LIKES[u1])) * math.sqrt(len(LIKES[u2])) )
    except ZeroDivisionError as zerr:
        print LIKES[u1], LIKES[u2]
        sys.exit(-1)

def neighborhood(LIKES, train_set, u):
    return dict({(n, cosine(LIKES, u, n)) for n in train_set})

def knn(LIKES, tv_watchers, test_set, user):
    neighbors = neighborhood(LIKES, tv_watchers.difference(test_set), user)
    return sorted([(k, v) for (k, v) in neighbors.iteritems() if v > 0.0], key=lambda tup: -tup[1]) # '-' sign to do reverse sort

def recommendations(LIKES, neighborhood, max_neighbors=10):
    recos = set([])
    for (neighbor, score) in neighborhood[:max_neighbors]:
        recos = recos.union(LIKES[neighbor])
    return recos

def evaluate(LIKES, tv_watchers, test_set, user):
    """
    For the given test user, temporarily hold back half the TV_SHOWS shows he has watched;
    then train (compute neighborhood) using the rest of the data. Next, generate
    recommendations for the test user and see how they compared to the held out set.
    """
    sample_size = int(math.ceil(0.5 * len(LIKES[user])))
    held_out = random.sample( LIKES[user], sample_size )
    LIKES[user] = LIKES[user].difference(held_out)
    neighborhood = knn(LIKES, tv_watchers, test_set, user)
    recos = recommendations(LIKES, neighborhood)
    if len(recos) == 0: return (0, 0)
    # precision = fraction of recos that are purchased
    precision = len(recos.intersection(LIKES[user].union(held_out))) / len(recos)
    # recall = fraction of purchased items returned by the recommender
    recall = len(recos.intersection(held_out)) / len(held_out)
    # restore user's shows
    LIKES[user] = LIKES[user].union(held_out)
    return precision, recall
                                   
def parse(fbDataFile, stopwords, UserUser=True):
    TV_SHOWS = {}
    LIKES = {}
    showId = 0
    tree = ET.parse(fbDataFile)
    root = tree.getroot()
    for user in root.findall('user'):
        userId = None
        tvShows = None
        about = None
        try:
            userId = user.attrib['id']
            tvShows = encode( normalize( tokenize(user.find('tv').text, ',') ) )
        except UnicodeEncodeError as uerr:
            pass
        showId = addTvShows(TV_SHOWS, showId, LIKES, userId, tvShows)
    if UserUser: return TV_SHOWS, LIKES
    # Item-Based
    LIKED_BY = addItems(LIKES)
    return TV_SHOWS, LIKED_BY
        
def main(argv):
    if len(argv) > 1:
        print "Usage: Recommender.py <fbDataFile.xml>"
        sys.exit(0)
    stopwords = set( open('/Users/samir_bajaj/stanford-ml/project/stop_words.txt', 'r').read().strip().split(',') )
    TV_SHOWS, LIKES = parse(argv[0], stopwords) #, False)    
    #
    total_precision = 0.0
    total_recall = 0.0
    for i in xrange(10):
        tv_watchers = set([u for u in LIKES.keys() if len(LIKES[u]) > 1]) # 4413 users with two or more TV_SHOWS likes
        test_set = set(sample(tv_watchers, 0.3))
        aggr_precision = 0.0
        aggr_recall = 0.0
        for u in test_set:
            (precision, recall) = evaluate(LIKES, tv_watchers, test_set, u)
            aggr_precision += precision
            aggr_recall += recall
        total_precision += aggr_precision/len(test_set)
        total_recall += aggr_recall/len(test_set)
    P = total_precision/10
    R = total_recall/10
    print P, R, (2 * P * R)/(P + R)


if __name__ == '__main__':
    main(sys.argv[1:])
