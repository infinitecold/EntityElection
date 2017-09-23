import random
import re
import requests
import time

def random_user_agent():
    user_agents = \
        ["Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
         "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36",
         "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2226.0 Safari/537.36",
         "Mozilla/5.0 (Windows NT 6.4; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36",
         "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
         "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0",
         "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0",
         "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko",
         "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 7.0; InfoPath.3; .NET CLR 3.1.40767; Trident/6.0; en-IN)",
         "Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)",
         "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A"]
    return random.choice(user_agents)

class GoogleVoter:
    def __init__(self):
        self.session = requests.Session()

    def get_wiki_names(self, search_term, count):
        url = "http://www.google.com/search?q="
        names = []
        is_blocked = True
        wait = 0
        
        while is_blocked == True:
            time.sleep(wait)
            self.session.headers.update({"User-Agent": random_user_agent()})
            r = self.session.get(url + search_term + " wiki", verify=False)  # possibly use site:wikipedia.org
            raw_html = r.text

            for iteration in re.finditer('<a href="', raw_html):
                end = raw_html.find('"', iteration.end())
                link = raw_html[iteration.end():end]

                # only keep wikipedia links
                if "wikipedia.org/" in link:
                    name = link.split('/')[4].replace('_', ' ')  # get the name of the article
                    names.append(name)
            
            if raw_html.find("Our systems have detected unusual traffic from your computer network.") == -1:
                is_blocked = False  # search went through
            else:
                wait += random.randint(3600, 18000)
                print("WAITING FOR " + str(wait) + " SECONDS BEFORE RETRYING GOOGLE QUERY...")

        return names[0:count]

class WikipediaVoter:
    lang = "en"  # default language

    def __init__(self, lang):
        self.lang = lang

    def get_wiki_names(self, search_term, count):
        url = "https://" + self.lang + ".wikipedia.org/w/index.php?fulltext=1&search=" + search_term
        names = []

        r = requests.get(url, verify=False)
        raw_html = r.text
        start = raw_html.find("<ul class='mw-search-results'>")  # identifier for search results titles
        end = raw_html.find("</ul>", start)
        raw_results = raw_html[start:end]

        for iteration in re.finditer('title="', raw_results):
            index = raw_results.find('"', iteration.end())
            title = raw_results[iteration.end():index]
            names.append(title.strip())

        return names[0:count]
