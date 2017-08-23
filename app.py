# We need to import request to access the details of the POST request
# and render_template, to render our templates (form and response)
# we'll use url_for to get some URLs for the app on the templates
from flask import Flask, render_template, request, url_for
import sys
import util
import json
import pickle
import random
import logging

import logging
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
logger = logging.getLogger()

#fileHandler = logging.FileHandler("app.log")
#fileHandler.setFormatter(logFormatter)
#logger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(logging.INFO)


# Initialize the Flask application
app = Flask(__name__)

# Define a route for the default URL, which loads the form
@app.route('/') # First page 
def form():
    return render_template('form_submit.html')

@app.route('/userClaimsInput/', methods=['POST'])
def userClaimsInput():
    QS=request.form['claim']
    print ("Query string is")
    print QS
    print request.form["button"]
    
    if request.form["button"] == "Try a Random Claim":
        list_claims = pickle.load(open('list_claim.pkl'))
        QS = random.choice(list_claims)
    return render_template('form_action.html', QueryString=QS)

# Second Page code down below 
#Error needs to be fixed using OOP


@app.route('/results/')
def results():
    claim = request.args['claim']
    res = util.get_res(claim)
    res_str = json.dumps(res, indent=4, sort_keys=True)
    headlines = [a['headlines'] for a in res['articles']]
    sources = [a['sources'] for a in res['articles']]
    stances = [ [s*100 for s in a['stance'] ] for a in res['articles']]
    veracity = [v*100 for v in res['veracity']]
    n = len(sources)

    return render_template("results.html", res=res_str, headlines=headlines, sources=sources, n=n,\
        veracity=veracity, stances=stances, claim=claim)


@app.route('/survey/')
def survey():
    return render_template("survey.html")

@app.route('/finish/')
def finish():
    useful = request.args.get('useful')
    easy = request.args.get('easy')
    comment = request.args.get('comment')
    
    log = "[SURVEY] useful=" + useful + ";easy=" + easy + ";comment=" + comment
    
    print log
    logger.info(log)
    
    return render_template("finish.html")


@app.route('/userClaimsOpinion/', methods=['POST'])
def userClaimsOpinion():
    EM = "The numbers should add up to 100!"
    truePercentage=request.form['trueInput']
    falsePercentage=request.form['falseInput']
    uncertainPercentage=request.form['unsureInput']
    total = int(truePercentage) + int(falsePercentage) + int(uncertainPercentage)
    if total != 100:
     return render_template('form_action.html', ErrorMessage=EM)   
    else:
        return render_template('form_action.html')



    # sum =int(QS) + int(QS2)

    # if sum >100 or sum<100:
    #     return render_template (userClaimsInput page , errormessage="The numbers should add up to 100")

    #In string QS, replace every string with a + and then pass it as a parameter to the API (An) 
    # QSNEW= "http://www.cs.utexas.edu/~atn/cgi-bin/api.cgi?claim="+ourstring
    
    
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=80)
