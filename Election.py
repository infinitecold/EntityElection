from collections import OrderedDict
import ConfigParser
import io
import MySQLdb
import random
import requests
import sys
import time
from Voters import GoogleVoter, WikipediaVoter

requests.packages.urllib3.disable_warnings()  # suppress warnings generated by requests package

# ugly solution to ensure unicode encoding
reload(sys)
sys.setdefaultencoding('utf-8')


# CONSTANTS AND TUNING PARAMETERS
NUM_OF_SEARCH_RESULTS = 3  # for each voter
DECAY = 0.95
WIKIPEDIA_FACTOR = 0.75  # multiplication factor to all values
GOOGLE_FACTOR = 1
ADJACENT_FACTOR = 0.6
INDIVIDUAL_FACTOR = 1
ENTITY_DISTANCE_THRESHOLD = 75  # distance between entity offsets in order to put together


# METHODS
def collect_votes(entity, search, is_adjacent, freebase_ids):
    # entity -> wiki name (via Wikipedia or Google)
    if search == "WIKIPEDIA":
        names = wikipedia.get_wiki_names(entity, NUM_OF_SEARCH_RESULTS)
        if not is_adjacent:
            weighting = [(DECAY**n)*WIKIPEDIA_FACTOR*ADJACENT_FACTOR for n in range(NUM_OF_SEARCH_RESULTS)]
        else:
            weighting = [(DECAY**n)*WIKIPEDIA_FACTOR*INDIVIDUAL_FACTOR for n in range(NUM_OF_SEARCH_RESULTS)]
    elif search == "GOOGLE":
        names = google.get_wiki_names(entity, NUM_OF_SEARCH_RESULTS)
        if not is_adjacent:
            weighting = [(DECAY**n)*GOOGLE_FACTOR*ADJACENT_FACTOR for n in range(NUM_OF_SEARCH_RESULTS)]
        else:
            weighting = [(DECAY**n)*GOOGLE_FACTOR*INDIVIDUAL_FACTOR for n in range(NUM_OF_SEARCH_RESULTS)]

    for count, wiki_name in enumerate(names):
        if wiki_name in cache:
            freebase_id = cache[wiki_name]
            print("{0} {1}. {2}\t{3}".format(search, count+1, wiki_name, cache[wiki_name]))
        else:
            # wiki name -> wiki ID
            wiki_url = "https://" + LANG + ".wikipedia.org/w/?title=" + wiki_name + "&action=info"
            r = requests.get(wiki_url)
            raw_html = r.text
            start = raw_html.find('<tr id="mw-pageinfo-article-id">')  # identifier for page ID
            end = raw_html.find("</td></tr>", start)
            if LANG == "es":
                wiki_id = raw_html[start+100:end]
            elif LANG == "zh":
                wiki_id = raw_html[start+78:end]
            else:  # since default language is english
                wiki_id = raw_html[start+81:end]

            # wiki ID -> freebase ID
            cur.execute("SELECT * FROM " + IDs_table + " WHERE `pageid` = " + wiki_id)
            row = cur.fetchone()
            if row is not None:  # if no result is found in MySQL, the result is NoneType
                freebase_id = row[0]
            else:
                freebase_id = "None"
                
            # save to cache
            cache[wiki_name] = freebase_id
            with io.open(CACHE_FILEPATH, 'a') as output_cache:
                output_cache.write(wiki_name + '\t' + freebase_id + '\n')
            
            print("{0} {1}. {2}\t{3}\t{4}".format(search, count+1, wiki_name, wiki_id, freebase_id))

        # tabulate scores
        if freebase_id != "None":
            if freebase_id not in freebase_ids:
                freebase_ids[freebase_id] = 0
            score = freebase_ids[freebase_id]
            score = score + weighting[count]
            freebase_ids[freebase_id] = score

    return freebase_ids


# VARIABLES
# filepaths and language
if len(sys.argv) == 1 or len(sys.argv) > 4:  # makes sure the correct number of arguments were specified
    #print("USAGE:\tpython [path to file]\n\tpython [path to file] [start index]\n\tpython [path to file] [start index] [end index]")
    print("USAGE:  {0}\n\t{0} {1}\n\t{0} {1} {2}".format("python [path to file]", "[start index]", "[end index]"))
    sys.exit()

INPUT_FILEPATH = sys.argv[1] #"/eecs/research/asr/fwei/KBP/elCandidate/elCandidateProj/data/iFlyTek16/eng/edl_fuse.cluster.tsv.selected.eng"
CACHE_FILEPATH = "cache.log"

LANG = "en"  # set language based on filepath with default as english 
if "cmn" in INPUT_FILEPATH:
    LANG = "zh"
elif "spa" in INPUT_FILEPATH:
    LANG = "es"

# data structures and objects
cache = {}
documents = OrderedDict()
google = GoogleVoter()
wikipedia = WikipediaVoter(LANG)

# MySQL
config = ConfigParser.RawConfigParser()
config.read("config.ini")
db = MySQLdb.connect(host=config.get("MySQL", "host"),
                     port=int(config.get("MySQL", "port")),
                     user=config.get("MySQL", "user"),
                     passwd=config.get("MySQL", "passwd"),
                     db=config.get("MySQL", "db"))
IDs_table = "WikiID" + LANG.upper()
cur = db.cursor()


# MAIN
with io.open(INPUT_FILEPATH, 'r', encoding='utf-8') as input_file, io.open(CACHE_FILEPATH, 'r') as input_cache:
    # read from cache
    for line in input_cache:
        line_data = line.split('\t')
        cache[line_data[0].rstrip()] = line_data[1].rstrip()
    
    # read from input file and retrieve all documents
    for line in input_file:
        line_data = line.split('\t')
        document_data = line_data[3].split(':')
        document = document_data[0]
        if document not in documents:
            documents[document] = OrderedDict()
        document_offset = document_data[1]
        entity = line_data[2]
        entities = documents[document]
        entities[document_offset] = entity  # add entity to document in documents
        documents[document] = entities

# process indices
if len(sys.argv) > 3:
    MAX_INDEX = int(sys.argv[3])
else:
    MAX_INDEX = len(documents)
if len(sys.argv) > 2:
    MIN_INDEX = int(sys.argv[2])
else:
    MIN_INDEX = 0

for index, (document, info) in enumerate(documents.iteritems()):
    if index >= MIN_INDEX and index < MAX_INDEX:
        for count, (document_offset, entity) in enumerate(info.iteritems()):
            print("DOCUMENT {0}: {1} ({2})".format(document, entity, document_offset))

            candidate_list = {}
            searches = 0
            # search with previous entity
            if count != 0:
                previous_indices = info.items()[count-1][0]
                previous_entity = info.items()[count-1][1]
                if int(document_offset.split('-')[0]) - int(previous_indices.split('-')[1]) < ENTITY_DISTANCE_THRESHOLD:
                    with_previous = previous_entity + " " + entity
                    print("'{0}':".format(with_previous))
                    candidate_list = collect_votes(with_previous, "WIKIPEDIA", True, candidate_list) 
                    candidate_list = collect_votes(with_previous, "GOOGLE", True, candidate_list)
                    searches += 1
                    time.sleep(random.uniform(1, 3))  # wait a random time in seconds in this range

            # search by itself
            print("'{0}':".format(entity))
            candidate_list = collect_votes(entity, "WIKIPEDIA", False, candidate_list)
            candidate_list = collect_votes(entity, "GOOGLE", False, candidate_list)
            searches += 1
            time.sleep(random.uniform(1, 3))  # wait a random time in seconds in this range

            # search with following entity
            if count != len(info)-1:
                following_indices = info.items()[count+1][0]
                following_entity = info.items()[count+1][1]
                if int(following_indices.split('-')[0]) - int(document_offset.split('-')[1]) < ENTITY_DISTANCE_THRESHOLD:
                    with_following = entity + " " + following_entity
                    print("'{0}':".format(with_following))
                    candidate_list = collect_votes(with_following, "WIKIPEDIA", True, candidate_list)
                    candidate_list = collect_votes(with_following, "GOOGLE", True, candidate_list)
                    searches += 1
                    time.sleep(random.uniform(1, 3))  # wait a random time in seconds in this range

            sorted_list = OrderedDict()
            for candidate, score in sorted(candidate_list.iteritems(), key=lambda(k,v): (v,k), reverse=True):
                sorted_list[candidate] = round(score*(3/searches), 3)  # normalize scores based on number of searches
                #print("{0}: {1:.3f}".format(candidate, sorted_list[candidate]))
            print("CANDIDATE LIST: {0}\n".format(sorted_list))
            
    elif index >= MAX_INDEX:
        break
