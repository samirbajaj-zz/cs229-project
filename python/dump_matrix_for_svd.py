"""
A script to write out the sparse Utility matrix of ~12,000 users x ~9,000 TV shows.

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
                             
def parse(fbDataFile, stopwords, UserUser=True):
    TV_SHOWS = {}
    LIKES = {}
    FEATURES = {}
    showId = 0
    tree = ET.parse(fbDataFile)
    root = tree.getroot()
    for user in root.findall('user'):
        userId = None
        tvShows = None
        try:
            userId = user.attrib['id']
            tvShows = encode( normalize( tokenize(user.find('tv').text, ',') ) )
        except UnicodeEncodeError as uerr:
            pass
        showId = addTvShows(TV_SHOWS, showId, LIKES, userId, tvShows)
    return TV_SHOWS, LIKES
        
def main(argv):
    if len(argv) > 1:
        print "Usage: Recommender.py <fbDataFile.xml>"
        sys.exit(0)
    stopwords = set( open('/Users/samir_bajaj/stanford-ml/project/stop_words.txt', 'r').read().strip().split(',') )
    TV_SHOWS, LIKES = parse(argv[0], stopwords)
    for u in LIKES.keys():
        ll = ['0']*5892
        for x in LIKES[u]: ll[x-1] = '1'
        print ' '.join(ll)



if __name__ == '__main__':
    main(sys.argv[1:])
