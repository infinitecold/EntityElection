import argparse
from collections import OrderedDict
import io
import logging
import sys


# CONSTANTS AND TUNING PARAMETERS
NUM_OF_SEARCH_RESULTS = 3
DECAY = 0.95
WIKIPEDIA_FACTOR = 0.75  # multiplication factor to all values depending on search method
GOOGLE_FACTOR = 1.00
ADJACENT_FACTOR = 0.50
INDIVIDUAL_FACTOR = 1.00
ENTITY_DISTANCE_THRESHOLD = 60  # distance between entity offsets in order to put together
NIL_THRESHOLD = 2.00


# INITIALIZATION
# ensures unicode encoding
reload(sys)
sys.setdefaultencoding("utf-8")

# initializes the logger
logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.INFO)

# parses command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('inputfilepath', type=str, help='filepath to .txt file to be processed')
parser.add_argument('--outputfilepath', type=str, default="../data/results/out.txt", help='filepath to output .txt file')
parser.add_argument('--cachefilepath', type=str, default="../data/cache/Election.cache", help='filepath to .cache file')
parser.add_argument('--lang', type=str, default="en", help='language of input file')
args = parser.parse_args()


# VARIABLES
TEAM_NAME = "iNCML0"

# data structures and objects
cache = {}
documents = OrderedDict()
nil_cache = {}  # saves NIL entities

# METHODS
def collect_votes(query, is_adjacent, candidate_list):
    if query not in cache:
        logging.info("NOT FOUND IN CACHE: {0}".format(query))
    else:
        wikipedia_ids, google_ids = cache[query]
        if is_adjacent:
            # search wikipedia
            weighting = [(DECAY**n)*WIKIPEDIA_FACTOR*ADJACENT_FACTOR for n in range(NUM_OF_SEARCH_RESULTS)]
            candidate_list = tabulate_scores(wikipedia_ids, weighting, candidate_list)
            # search google
            weighting = [(DECAY**n)*GOOGLE_FACTOR*ADJACENT_FACTOR for n in range(NUM_OF_SEARCH_RESULTS)]
            candidate_list = tabulate_scores(google_ids, weighting, candidate_list)
        else:
            # search wikipedia
            weighting = [(DECAY**n)*WIKIPEDIA_FACTOR*INDIVIDUAL_FACTOR for n in range(NUM_OF_SEARCH_RESULTS)]
            candidate_list = tabulate_scores(wikipedia_ids, weighting, candidate_list)
            # search google
            weighting = [(DECAY**n)*GOOGLE_FACTOR*INDIVIDUAL_FACTOR for n in range(NUM_OF_SEARCH_RESULTS)]
            candidate_list = tabulate_scores(google_ids, weighting, candidate_list)
    return candidate_list

def tabulate_scores(ids, weighting, candidate_list):
    for count, freebase_id in enumerate(ids):
        if count >= NUM_OF_SEARCH_RESULTS:
            break
        if freebase_id != "None":
            if freebase_id not in candidate_list:
                candidate_list[freebase_id] = 0
            score = candidate_list[freebase_id]
            score = score + weighting[count]
            candidate_list[freebase_id] = score
            logging.info("{0}: {1}".format(freebase_id, weighting[count]))
    return candidate_list

def determine_nil(entity, final_answer):
    if entity not in nil_cache:
        final_answer = final_answer + str(len(nil_cache))
        nil_cache[entity] = final_answer
    else:
        final_answer = nil_cache[entity]
    return final_answer

# MAIN
with open(args.cachefilepath, 'r') as input_cache:
    # read from cache file
    for line in input_cache:
        line.decode("utf-8")
        line_data = line.split('\t')
        cache[line_data[0].strip()] = (line_data[1].strip().split(','), line_data[2].strip().split(','))

with open(args.inputfilepath, 'r') as input_file:
    # read from input file and retrieve all documents and their associated entities
    for line in input_file:
        line.decode("utf-8")
        line_data = line.split('\t')
        document_data = line_data[3].split(':')
        document = document_data[0]
        if document not in documents:
            documents[document] = []
        # document_info format: (name, offset, entity type (ORG, PER, etc.), entity type (NAM/NOM))
        document_info = (line_data[2], document_data[1], line_data[5], line_data[6])
        entities = documents[document]  # retrieve existing entities associated with the document
        entities.append(document_info)  # add current entity 
        documents[document] = entities

for document, info in documents.iteritems():
    for index, entity in enumerate(info):
        candidate_list = {}
        entity_name = entity[0]
        offset = entity[1]
        searches = 0
        logging.info("DOCUMENT {0}: {1} ({2})".format(document, entity_name, offset))
            
        # search with previous entity
        if index != 0:
            previous_offset = info[index-1][1]
            offset_difference = int(offset.split('-')[0]) - int(previous_offset.split('-')[0])
            if offset_difference > 0 and offset_difference < ENTITY_DISTANCE_THRESHOLD:
                with_previous = info[index-1][0] + " " + entity_name
                logging.info("SEARCHED (with previous): '{0}' ({1})".format(with_previous, offset_difference))
                candidate_list = collect_votes(with_previous, True, candidate_list)
                searches += 1
                
        # search by itself
        logging.info("SEARCHED (by itself): '{0}'".format(entity_name))
        candidate_list = collect_votes(entity_name, False, candidate_list)
        searches += 1

        # search with following entity
        if index != len(info)-1:
            following_offset = info[index+1][1]
            offset_difference = int(following_offset.split('-')[0]) - int(offset.split('-')[0])
            if offset_difference > 0 and offset_difference < ENTITY_DISTANCE_THRESHOLD:
                with_following = entity_name + " " + info[index+1][0]
                logging.info("SEARCHED (with following): '{0}' ({1})".format(with_following, offset_difference))
                candidate_list = collect_votes(with_following, True, candidate_list)
                searches += 1
            
        # choose best candidate/NIL
        sorted_list = []
        final_answer = "NIL"
        if len(candidate_list) > 0:
            for candidate, score in sorted(candidate_list.iteritems(), key=lambda(k,v): (v,k), reverse=True):
                sorted_list.append((candidate, round(score*(3/searches), 4)))  # normalize scores based on number of searches
            if sorted_list[0][1] > NIL_THRESHOLD:
                final_answer = sorted_list[0][0]
            else:
                final_answer = determine_nil(entity_name, final_answer)
        else:
            final_answer = determine_nil(entity_name, final_answer)

        logging.info("FINAL ANSWER: {0}".format(final_answer))
        logging.info("CANDIDATE LIST: {0}\n".format(sorted_list))
            
        with open(args.outputfilepath, 'a') as output_file:
            output_file.write("{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\n".format(TEAM_NAME, "TRAINING",
                                                                                entity_name, document + ":" + offset,
                                                                                final_answer, entity[2],
                                                                                entity[3], "1.0").encode("utf-8"))
