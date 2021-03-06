import argparse
import ConfigParser
import io
import logging
import MySQLdb
import random
import requests
import sys
import time
import urllib
import types
from Voters import GoogleVoter, WikipediaVoter


# INITIALIZATION
# suppresses warnings generated by requests package
requests.packages.urllib3.disable_warnings()

# ensures unicode encoding
reload(sys)
sys.setdefaultencoding("utf-8")

# initializes the logger
logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.INFO)
logging.getLogger("requests").setLevel(logging.WARNING)

# parses command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('inputfilepath', type=str, help='filepath to .txt file to be processed')
parser.add_argument('--lang', type=str, default="en", help='language of input file')
parser.add_argument('--cachefilepath', type=str, default="../data/cache/Election.cache", help='filepath to .cache file')
parser.add_argument('--startindex', type=int, default=0, help='start index of generated queries to be searched')
parser.add_argument('--endindex', type=int, default=sys.maxint, help='end index of generated queries to be searched')
args = parser.parse_args()


# VARIABLES
NUM_OF_SEARCH_RESULTS = 5  # maximum for each voter

# Data structures and objects
cache = []
entities = []  # raw entities from the input file
queries = []  # assembled queries using the entities
google = GoogleVoter()
wikipedia = WikipediaVoter(args.lang)

# MySQL
config = ConfigParser.RawConfigParser()
config.read("/eecs/home/kelvin/EntityElection/config.ini")

KBP15_db = MySQLdb.connect(host=config.get("KBP15", "host"),
                           port=int(config.get("KBP15", "port")),
                           user=config.get("KBP15", "user"),
                           passwd=config.get("KBP15", "passwd"),
                           db=config.get("KBP15", "db"))
wiki2freebase_table = "WikiID" + args.lang.upper()
KBP15_cur = KBP15_db.cursor()

freebase_db = MySQLdb.connect(host=config.get("Freebase", "host"),
                              port=int(config.get("Freebase", "port")),
                              user=config.get("Freebase", "user"),
                              passwd=config.get("Freebase", "passwd"),
                              db=config.get("Freebase", "db"))
name2id_table = "freebase-onlymid_-_en_name2id"
id2rowid_table = "freebase-onlymid_-_fb-id2row-id"
datadump_table = "freebase-onlymid_-_datadump"
freebase_cur = freebase_db.cursor()


# METHODS
def search(query):
    # query -> wiki names (via Wikipedia and Google)
    logging.info("QUERY: {0}".format(query))
    wikipedia_names = wikipedia.get_wiki_names(query, NUM_OF_SEARCH_RESULTS)
    wikipedia_ids = get_freebase_ids(wikipedia_names, "WIKI")

    google_names = google.get_wiki_names(query, NUM_OF_SEARCH_RESULTS)
    google_ids = get_freebase_ids(google_names, "GOOGLE")

    return wikipedia_ids, google_ids

def get_freebase_ids(wiki_names, site):
    freebase_ids = []
    for count, wiki_name in enumerate(wiki_names):
        # wiki name -> wiki ID
        wiki_name = wiki_name.decode('utf8','ignore')
        wiki_url = "https://" + args.lang + ".wikipedia.org/w/?title=" + wiki_name + "&action=info"

        r = requests.get(wiki_url)
        raw_html = r.text
        start = raw_html.find('<tr id="mw-pageinfo-article-id">')  # identifier for page ID
        end = raw_html.find("</td></tr>", start)

        if start != -1 and end != -1: 
            wiki_id = raw_html[start:end].split('>')[4]  # manually retrieves wiki ID from raw HTML
        else:
            wiki_id = 0

        # wiki ID -> freebase ID
        KBP15_cur.execute("SELECT * FROM {0} WHERE `pageid` = {1}".format(wiki2freebase_table, wiki_id))
        row = KBP15_cur.fetchone()  

        freebase_id = "None"
        if row is not None :  # if no result is found in MySQL, the result is NoneType
            freebase_id = row[0]
        else:  # otherwise, check Freebase
            wiki_name = wiki_name.replace("'", "\\'")
            wiki_name = wiki_name.replace('"', '\"')
            freebase_cur.execute("""SELECT * FROM `{0}` WHERE `en_name` = '"{1}"@en'""".format(name2id_table, wiki_name))
            row = freebase_cur.fetchone()  # gets list of possible freebase IDs

            if row is not None:
                possible_ids = row[1].split(',')
                for possible_id in possible_ids:
                    possible_id = possible_id[0:possible_id.index('(')]
                    freebase_cur.execute("SELECT * FROM `{0}` WHERE `freebase_id` = '<http://rdf.freebase.com/ns/{1}>'".format(id2rowid_table, possible_id))
                    row = freebase_cur.fetchone()  # gets min and max row IDs for the current freebase ID
                    if row is not None:
                        min_row = row[1]
                        max_row = row[2]
                        freebase_cur.execute("SELECT * FROM `{0}` WHERE `row_id` > {1} AND `row_id` < {2}".format(datadump_table, min_row, max_row))
                        results = freebase_cur.fetchall();  # gets all triples for the current freebase ID
                        for row in results:
                            #if row[1] == "<http://rdf.freebase.com/ns/common.topic.topic_equivalent_webpage>" and wiki_id in row[2]:
                            wiki_name2 = wiki_name.replace(' ','_')
                            wiki_name2 = urllib.quote(wiki_name2.encode('latin-1','ignore'))

                            wiki_url_en = "<http://en.wikipedia.org/wiki/" + wiki_name2 + ">"
                            wiki_url_zh = "<http://zh.wikipedia.org/wiki/" + wiki_name2 + ">"
                            wiki_url_es = "<http://es.wikipedia.org/wiki/" + wiki_name2 + ">"
                            topic_webpage = "common.topic.topic_equivalent_webpage" 

                            if topic_webpage in row[1]:
                                if row[2] == wiki_url_en or row[2] == wiki_url_zh: # or row[2] == wiki_url_es:
                                    freebase_id = possible_id
                                    break;

        freebase_ids.append(freebase_id)
        logging.info("{0}{1}. {2}\t{3}\t{4}".format(site, count+1, wiki_name, wiki_id, freebase_id))
        
    return freebase_ids


# MAIN
with open(args.cachefilepath, 'r') as input_cache:
    # read from cache file and retrieve all cached queries
    for line in input_cache:
        line.decode("utf-8")
        line_data = line.split('\t')
        cache.append(line_data[0].strip())

with open(args.inputfilepath, 'r') as input_file:    
    # read from input file and retrieve all entities
    for line in input_file:
        line.decode("utf-8")
        line_data = line.split('\t')
        entity = line_data[2]
        entities.append(entity)

# assemble all combinations of entities
for count, entity in enumerate(entities):
    # assemble with previous
    if count != 0:
        queries.append(entities[count-1] + " " + entity)
    # by itself
    queries.append(entity)
    # assemble with following
    if count != len(entities)-1:
        queries.append(entity + " " + entities[count+1])

# get unique queries by converting list to set to list, which also shuffles items
logging.info("NUMBER OF NON-UNIQUE QUERIES: {0}".format(len(queries)))
queries = list(set(queries))
logging.info("NUMBER OF UNIQUE QUERIES: {0}".format(len(queries)))

# if an end index isn't specified or is out of range, change to length of queries
if args.endindex > len(queries):
    args.endindex = len(queries)

# make sublist of queries based on indices, if provided
sub_queries = queries[args.startindex:args.endindex]

for query in sub_queries:    
    # if query is already in cache, it can be skipped
    if query not in cache:
        wikipedia_ids, google_ids = search(query)
        with open(args.cachefilepath, 'a') as output_cache:
            output_cache.write("{0}\t{1}\t{2}\n".format(query, ','.join(wikipedia_ids), ','.join(google_ids)).encode("utf-8"))
        logging.info("SAVED TO CACHE: {0}\t{1}\t{2}\n".format(query, ','.join(wikipedia_ids), ','.join(google_ids)))
        cache.append(query)
        time.sleep(random.uniform(10, 20))  # wait a random time in seconds in this range
    else:
        logging.info("FOUND '{0}' IN CACHE, SKIPPING...\n".format(query))

logging.info("CACHE GENERATION COMPLETE")
