#!/bin/sh

#datafile="~/EntityElection/data/window3-0.786-resorted.data"
#language=" --authorsfilepath ~/EntityElection/data/KBP16.authors --lang en --cachefilepath ~/EntityElection/data/cache/Election.cache" 
language=" --authorsfilepath /cs/research/asr/kelvin/KBP2017-eval/trial1/KBP2017-all.authors --lang en --cachefilepath /eecs/research/asr/kelvin/EntityElection-data/cache/KBP2017_ENG.cache"
eval_lang="16-eval/eng.tab"

#language=" --authorsfilepath /cs/home/kelvin/EntityElection/data/KBP16-cmn.authors --lang zh --cachefilepath /cs/home/kelvin/EntityElection/data/cache/kbp16-chinese2.cache"
#language=" --authorsfilepath /cs/research/asr/kelvin/KBP2017-eval/trial1/KBP2017-all.authors --lang zh --cachefilepath /eecs/research/asr/kelvin/EntityElection-data/cache/KBP2017_CMN.cache"
#eval_lang="16-eval/cmn.tab" 

#language=" --authorsfilepath /cs/home/kelvin/EntityElection/data/KBP16-spa.authors --lang es --cachefilepath /cs/home/kelvin/EntityElection/data/cache/kbp16-spanish2-2.cache"
#language=" --authorsfilepath /cs/research/asr/kelvin/KBP2017-eval/trial1/KBP2017-all.authors --lang es --cachefilepath /eecs/research/asr/kelvin/EntityElection-data/cache/KBP2017_SPA.cache"
#eval_lang="16-eval/spa.tab"

numres=5
decay=0.7
wikipedia=0.4
adjacent=0.4
distance=250
nil=0.9

echo "python ~/EntityElection/src/Election.py $1 --numofsearchresults $numres --decay $decay --wikipediafactor $wikipedia --adjacentfactor $adjacent --distancethreshold $distance --nilthreshold $nil $language "

python ~/EntityElection/src/Election.py $1 --numofsearchresults $numres --decay $decay --wikipediafactor $wikipedia --adjacentfactor $adjacent --distancethreshold $distance --nilthreshold $nil $language 

echo "~/EntityElection/src/evaluate.sh ~/EntityElection/data/results/$numres-$decay-$wikipedia-$adjacent-$distance-$nil.out $eval_lang"

~/EntityElection/src/evaluate.sh ~/EntityElection/data/results/$numres-$decay-$wikipedia-$adjacent-$distance-$nil.out $\
eval_lang

echo "mv -f ~/EntityElection/data/results/$numres-$decay-$wikipedia-$adjacent-$distance-$nil.out $2"

mv -f ~/EntityElection/data/results/$numres-$decay-$wikipedia-$adjacent-$distance-$nil.out $2

