#!/bin/sh

#datafile="~/EntityElection/data/window3-0.786-resorted.data"
#language=" --authorsfilepath ~/EntityElection/data/KBP16.authors --lang en --cachefilepath ~/EntityElection/data/cache/Election.cache" 
#eval_lang="16-eval/eng.tab"

#datafile="~/EntityElection/data/KBP16-cmn2.data"                                                      
#language=" --authorsfilepath ~/EntityElection/data/KBP16-cmn.authors --lang zh --cachefilepath ~/EntityElection/data/cache/kbp16-chinese2.cache"
#eval_lang="16-eval/cmn.tab" 

datafile="~/EntityElection/data/KBP16-spa2.data"                                                                  
language=" --authorsfilepath ~/EntityElection/data/KBP16-spa.authors --lang es --cachefilepath ~/EntityElection/data/cache/kbp16-spanish2.cache"                                                                                    
eval_lang="16-eval/spa.tab"


for numres in 5  # 5 3
do
    for decay in 0.8 0.7 0.6 # 0.9 0.8 0.7 0.5 0.3 
    do
	for wikipedia in  0.5 0.4 0.3   # 0.9 0.7 0.6 0.5 0.4
	do
	    for adjacent in 0.5 0.4 0.3  # 0.9 0.6 0.5 0.4 0.3 0.2  
	    do
		for distance in 250 200 150 #150 #120 100  # 100 80 50
		do
		    for nil in 1.4 1.2 0.9 0.8 #1.0 0.9 #0.8 #0.7 0.6 0.5 # 2.5 2.0 1.75 1.5 1.0 0.95 0.9 0.85 0.8
		    do
			#echo "$numres $decay $wikipedia $distance $adjacent $nil"
			echo "(source ~/.cshrc; virtual-python; python ~/EntityElection/src/Election.py $datafile --numofsearchresults $numres --decay $decay --wikipediafactor $wikipedia --adjacentfactor $adjacent --distancethreshold $distance --nilthreshold $nil $language >& /tmp/kelvin$$-window3-$numres-$decay-$wikipedia-$adjacent-$distance-$nil.log; ~/EntityElection/src/evaluate.sh ~/EntityElection/data/results/$numres-$decay-$wikipedia-$adjacent-$distance-$nil.out $eval_lang; \rm -rf ~/EntityElection/data/results/$numres-$decay-$wikipedia-$adjacent-$distance-$nil.out)"
		    done
		done
	    done
	done
    done
done