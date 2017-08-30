# Echo server program
import socket
import app2

import pickle
temp_res_g = pickle.load(open('temp_resg.pkl'))

import json

def api_call(claim):
    res_g = app2.query_g(claim)
    (sources, df, vera, stances, rep) = app2.answer(claim, res_g, True)
    articles = []
    n = len(sources)
    for i in range(n):
        a = {"sources": sources[i], "reputation": rep[i], "headlines": df.articleHeadline[i], "stance": stances[i].tolist() }
        articles.append(a)

    res = {"claim": claim,\
            "articles": articles, \
            "veracity": vera[0].tolist()
    }
    return res
    #return json.dumps(res)

def answer(data):
    # extract data
    a = data.split("\n")
    if a[0] == 'claim':
        uid = -1
        claim = a[1]
    elif a[0] == 'uc':
        uid = a[1]
        claim = a[2]
    elif a[0] == 'api':
        claim = a[1]
        return api_call(claim)
    # load db file
    db = pickle.load(open('/u/atn/public_html/cgi-bin/factdb.pkl'))
    try:
        print 'claim: ', claim
        res_g = app2.query_g(claim)
        print 'got res_g'
        #res_g = temp_res_g
        (sources, df, vera) = app2.answer(claim, res_g)
        
        print 'got (s, df, vera)'
        #save to db
        headlines = df.articleHeadline.values.tolist()
        db.update({uid: (sources, headlines, vera)})
        pickle.dump(db, open('/u/atn/public_html/cgi-bin/factdb.pkl','w') )

        ans_str = app2.gen_res_str(sources, df, vera)
        ans_str = ans_str.encode('ascii', 'ignore')
        return ans_str
    except:
        return ""

if False:
    HOST = ''                 # Symbolic name meaning all available interfaces
    PORT = 50007              # Arbitrary non-privileged port


    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(1)

    print 'ready'

    while True:
        conn, addr = s.accept()
        print 'Connected by', addr

        while True:
            data = conn.recv(pow(2,20))
            if not data: break
            print "received data:", data
            conn.sendall(answer(data))
        conn.close()
