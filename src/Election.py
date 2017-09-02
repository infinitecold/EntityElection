import argparse
from collections import OrderedDict
import io
import logging
import sys


# INITIALIZATION
# ensures unicode encoding
reload(sys)
sys.setdefaultencoding("utf-8")

# initializes the logger
logging.basicConfig(format='%(asctime)s\t%(message)s', level=logging.INFO)

# parses command-line arguments
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('inputfilepath', type=str, help='filepath to .txt file to be processed')
parser.add_argument('--outputfilepath', type=str, default="../data/results/out.txt", help='filepath to output .txt file')
parser.add_argument('--cachefilepath', type=str, default="../data/cache/Election.cache", help='filepath to .cache file')
parser.add_argument('--authorsfilepath', type=str, default="../data/KBP16.authors", help='filepath to .authors file')
parser.add_argument('--lang', type=str, default="en", help='language of input file')
# constants and tuning parameters
parser.add_argument('--numofsearchresults', type=int, default=3)
parser.add_argument('--decay', type=float, default=0.9)
parser.add_argument('--wikipediafactor', type=float, default=0.75)
parser.add_argument('--googlefactor', type=float, default=1.0)
parser.add_argument('--adjacentfactor', type=float, default=0.5)
parser.add_argument('--individualfactor', type=float, default=1.0)
parser.add_argument('--distancethreshold', type=int, default=50)
parser.add_argument('--nilthreshold', type=float, default=2.5)
args = parser.parse_args()


# VARIABLES
TEAM_NAME = "YorkU0"

# data structures and objects
cache = {}
authors = set()
documents = OrderedDict()
nil_cache = {}  # saves NIL entities


# METHODS
def collect_votes(query, adjacent_factor, candidate_list):
    if query not in cache:
        logging.info("NOT FOUND IN CACHE: {0}".format(query))
    else:
        wikipedia_ids, google_ids = cache[query]
        # search wikipedia
        weighting = [(args.decay**n)*args.wikipediafactor*adjacent_factor for n in range(args.numofsearchresults)]
        candidate_list = tabulate_scores(wikipedia_ids, weighting, candidate_list)
        # search google
        weighting = [(args.decay**n)*args.googlefactor*adjacent_factor for n in range(args.numofsearchresults)]
        candidate_list = tabulate_scores(google_ids, weighting, candidate_list)
    return candidate_list

def tabulate_scores(ids, weighting, candidate_list):
    for count, freebase_id in enumerate(ids):
        if count >= args.numofsearchresults:
            break
        if freebase_id != "None" and freebase_id != '':
            if freebase_id not in candidate_list:
                candidate_list[freebase_id] = 0
            candidate_list[freebase_id] += weighting[count]
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

with open(args.authorsfilepath, 'r') as input_authors:
    # read from authors file
    for line in input_authors:
        authors.add(line.strip())

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
        entity_info = (line_data[2], document_data[1], line_data[5], line_data[6])
        documents[document].append(entity_info)

for document, info in documents.iteritems():
    # nil_cache.update({}.fromkeys(nil_cache, "None"))  # clear values in nil cache
    final_answers = []
    for index, entity in enumerate(info):
        final_answer = "NIL"
        candidate_list = {}
        sorted_list = []
        norm_factor = 0
        logging.info("DOCUMENT {0}: {1} ({2}) [{3} {4}]".format(document, entity[0], entity[1], entity[2], entity[3]))
        if "{0}:{1}".format(document, entity[1]) in authors:
            logging.info("FOUND IN AUTHORS LIST")
            final_answer = determine_nil(entity[0], final_answer)
        else:  
            # search with previous entity
            if index != 0:
                previous_offset = info[index-1][1]
                offset_difference = int(entity[1].split('-')[0]) - int(previous_offset.split('-')[0])
                if offset_difference > 0 and offset_difference < args.distancethreshold:
                    with_previous = info[index-1][0] + " " + entity[0]
                    logging.info("SEARCHED (with previous): '{0}' [{1}]".format(with_previous, offset_difference))
                    candidate_list = collect_votes(with_previous, args.adjacentfactor, candidate_list)
                    norm_factor += args.adjacentfactor

            # search with following entity
            if index != len(info)-1:
                following_offset = info[index+1][1]
                offset_difference = int(following_offset.split('-')[0]) - int(entity[1].split('-')[0])
                if offset_difference > 0 and offset_difference < args.distancethreshold:
                    with_following = entity[0] + " " + info[index+1][0]
                    logging.info("SEARCHED (with following): '{0}' [{1}]".format(with_following, offset_difference))
                    candidate_list = collect_votes(with_following, args.adjacentfactor, candidate_list)
                    norm_factor += args.adjacentfactor
            
            if entity[3] == "NOM":  # if nominal entity
                # scan previous entities
                count = 0
                while count < index:
                    count += 1
                    previous_offset = info[index-count][1]
                    previous_type = (info[index-count][2], info[index-count][3])
                    offset_difference = int(entity[1].split('-')[0]) - int(previous_offset.split('-')[0])
                    if offset_difference < 2*args.distancethreshold:
                        if offset_difference > 0 and previous_type == (entity[2], "NAM"):
                            final_answer = final_answers[index-count]
                            if freebase_id not in candidate_list:
                                candidate_list[freebase_id] = 0
                            candidate_list[freebase_id] += args.individualfactor
                            norm_factor += args.individualfactor
                            logging.info("USING PREVIOUS {0} ({1}): {2}".format(final_answer, info[index-count][0], args.individualfactor))
                            break
                    else:
                        final_answer = determine_nil(entity[0], final_answer)
                        break
            else:  # if name entity
                # search by itself
                logging.info("SEARCHED (by itself): '{0}'".format(entity[0]))
                candidate_list = collect_votes(entity[0], args.individualfactor, candidate_list)
                norm_factor += args.individualfactor
            
            # choose best candidate/NIL
            if len(candidate_list) > 0:
                for candidate, score in sorted(candidate_list.iteritems(), key=lambda(k,v): (v,k), reverse=True):
                    # normalize scores based on number of searches
                    sorted_list.append((candidate, round(score*((2*args.adjacentfactor+args.individualfactor)/norm_factor), 4)))
                    if sorted_list[0][1] > args.nilthreshold:
                        final_answer = sorted_list[0][0]
                    else:
                        final_answer = determine_nil(entity[0], final_answer)
            else:
                final_answer = determine_nil(entity[0], final_answer)
        final_answers.append(final_answer)
            
        logging.info("FINAL ANSWER: {0}".format(final_answer))
        logging.info("CANDIDATE LIST: {0}\n".format(sorted_list))
            
        with open(args.outputfilepath, 'a') as output_file:
            output_file.write("{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\n".format(TEAM_NAME, "TRAINING", entity[0], 
                                                                                document + ":" + entity[1], final_answer, 
                                                                                entity[2], entity[3], "1.0").encode("utf-8"))
logging.info("ELECTION COMPLETE")
