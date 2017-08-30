#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon May 29 17:07:31 2017

@author: thanhan
"""

api_key = '3d94496b-9c20-4ae0-abb6-407f8f64c541'

import numpy as np

#from eventregistry import *

from urlparse import urlparse, parse_qs

from lxml.html import fromstring
from requests import get
import lxml.html
import urllib
import urllib2
import json
import requests
import sys
import pickle
import pandas as pd

import nltk
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('conll2002')
nltk.download('wordnet')
nltk.download('maxent_treebank_pos_tagger')
nltk.download('hmm_treebank_pos_tagger')






def query_er(claim):
    er = EventRegistry(apiKey = api_key)
    q = QueryArticlesIter(conceptUri = er.getConceptUri(claim))
    
    res = []
    for art in q.execQuery(er, sortBy = "date"):
        res.append(art)
        
    return res


def query_er2(claim):
    er = EventRegistry(apiKey = api_key)
    q = QueryArticles()
    # set the date limit of interest
    q.setDateLimit(datetime.date(2014, 4, 16), datetime.date(2014, 4, 28))
    # find articles mentioning the company Apple
    q.addConcept(er.getConceptUri("Apple"))
    # return the list of top 30 articles, including the concepts, categories and article image
    q.addRequestedResult(RequestArticlesInfo(page = 1, count = 30,
        returnInfo = ReturnInfo(articleInfo = ArticleInfoFlags(concepts = True, categories = True, image = True))))
    res = er.execQuery(q)


#pip install --upgrade google-api-python-client
g_api = 'AIzaSyDdcg5mQHVXKWvLIz-pMckpPLYghI3ptbs'

g_id = '000758571849911321468:shcsm3fdnds'

from googleapiclient.discovery import build


def get_title(url):
    
    try:
        page = urllib2.urlopen(url)
        t = lxml.html.parse(page)
        return t.find(".//title").text
    except Exception, e:
        print("Unexpected error:", e)
        return ""

def get_source(url):
    return url[ url.find('www') + 0 : url.find('.com') + 4]

def web_search(claim):
    url = 'https://www.google.com/search?'
    
    final_url = url + urllib.urlencode({'q': claim})
    
    raw = get(final_url).text
    page = fromstring(raw)

    res = []
    
    for result in page.cssselect(".r a"):
        url = result.get("href")
        if url.startswith("/url?"):
            url = parse_qs(urlparse(url).query)['q']
        res.append(url[0])
        
    return res
    
def web_search_title(claim):
    links = web_search(claim)
    titles = [get_title(l) for l in links]
    sources = [get_source(l) for l in links]
    
    return (links, titles, sources)



def query_g(claim):
    """
    get search results (from google)
    """
    list_claim = pickle.load(open('list_claim.pkl'))
    if claim in list_claim:
        # claim in the dataset, load it
        data_all = pd.read_csv('edata_all.csv')
        rel_data = data_all[ data_all.claimHeadline == claim]
        sources = rel_data.source.tolist()
        titles = rel_data.articleHeadline.tolist()
        res = {'items': [{'displayLink': s, 'title': t} for s, t in zip(sources, titles)]}
        return res

    try:
        # use google api
        #raise Exception('abc')
        service = build("customsearch", "v1", developerKey=g_api)
        res = service.cse().list( q=claim, cx=g_id).execute()
        if int(res['searchInformation']['totalResults']) == 0: raise Exception("no google res")
    except Exception, e:
        # fall back to directly scrape
        print "fall back to directly scrape"
        (links, titles, sources) = web_search_title(claim)
        res = {'items': [{'displayLink': s, 'title': t} for s, t in zip(sources, titles)]}

    return res




def process_g(g, claim):
    sources = []
    headlines= []
    
    for i in g['items']:
        source = i['displayLink']
        headline = i['title']
        #res.append((source, headline))
        sources.append(source)
        headlines.append(headline)
    
    n = len(sources)
    
    df = pd.DataFrame({ 'claimHeadline': [claim] * n, \
                        'articleHeadline': headlines, \
                        'claimId': [0] * n, \
                        'articleId': range(n) } )
    
    return (sources, df)

import features

train_data = features.get_dataset('url-versions-2015-06-14-clean-train.csv')
X, y = features.split_data(train_data)
X = features.p.pipeline.fit_transform(X)

def get_features(df):
    xt = features.p.pipeline.transform(df)
    return xt

def get_features_ch(claim, headline):
    df = pd.DataFrame({ 'claimHeadline': [claim], \
                        'articleHeadline': [headline], \
                        'claimId': [0], \
                        'articleId': [0] } )
    
    xt = features.p.pipeline.transform(df)
    return xt

def get_claim_f(dic_s, sources, stances, l = 724):
    f = np.zeros((1, 724))
    for so, st in zip(sources, stances):
        if so not in dic_s: continue
        sid = dic_s[so] - 1 # 1-index to 0-index
        f[0, sid] = st - 1 # 0, 1, 2 to -1, 0, 1
        
    return f


def get_rep(dic_s, sources, clf):
    res = []
    for so in sources:
        if so not in dic_s: 
            res.append(0)
            continue
        sid = dic_s[so] - 1 # 1-index to 0-index
        rep = sum(abs(clf.coef_[:, sid]))
        rep = 1 if rep > 1 else rep
        res.append(rep)
    return res


def answer(claim, res_g, for_api = False):
    """
    for_api: return results for api call
    """
    #(cmv, dic_s) = pickle.load(open('save_cmv_dics.pkl'))
    (clf_vera, clf_stance, dic_s) = pickle.load(open('save_clf_dics.pkl'))
    
    
    (sources, df) = process_g(res_g, claim)
    xt = get_features(df)
    
    stances = clf_stance.predict(xt)
    claim_f = get_claim_f(dic_s, sources, stances)
    
    vera = clf_vera.predict_proba(claim_f)
    rep = get_rep(dic_s, sources, clf_vera)
    
    if for_api:
        stances_p = clf_stance.predict_proba(xt)
        return (sources, df, vera, stances_p, rep)

    return (sources, df, vera)
    
    
def gen_res_str(sources, df, vera):
    headlines = df.articleHeadline
    
    res = ""
    for s, h in zip(sources, headlines):
        res = res + s + ': ' + h + '<br>'
    
    pf = int(vera[0][0]* 100)
    pu = int(vera[0][1]* 100)
    pt = int(vera[0][2]* 100)
    res = res + 'Predict veracity: ' + str(pf) + '% False, ' + \
                                    str(pu) + '% Unknown, ' +  \
                                    str(pt) + '% True, '
    
    return res
    
    
def web_search2(claim):
    url = 'https://www.google.com/search?'
    
    final_url = url + urllib.urlencode({'q': claim})
    
    response = requests.get(final_url)
    
    html = response.text
    
    return html




