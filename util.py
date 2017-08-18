import urllib
import urllib2
import json


def get_res(claim):
    """
    get results for a claim,
    using the API
    """
    
    url = 'http://www.cs.utexas.edu/~atn/cgi-bin/api.cgi?'
    
    final_url = url + urllib.urlencode({'claim': claim})
    
    response = urllib2.urlopen(final_url)
    
    html = response.read()
    
    content = html[ html.find('</head>') + 9 : -2]
    
    content2 = content.replace('\\', '')
    
    res = json.loads(content2)
    
    return res
