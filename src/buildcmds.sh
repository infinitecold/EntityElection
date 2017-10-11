#!/bin/sh

# $1: run ID, $2: total number of unique entities, $3: number of subsets to be run, $4: full filepath of data file
i=`expr $2 / $3`
count=`expr $i + 1`

j=`expr $3 - 1`
for k in `seq 0 $j`;
do
    start=`expr $k \* $count`
    end=`expr $start + $count`
    m=`expr $k + 1`
    echo "(source ~/.cshrc; virtual-python; touch /eecs/home/kelvin/EntityElection/data/cache/run$1-$m.cache; python /eecs/home/kelvin/EntityElection/src/CacheGeneration.py $4 --cachefilepath /eecs/home/kelvin/EntityElection/data/cache/run$1-$m.cache --startindex $start --endindex $end >& /eecs/home/kelvin/EntityElection/data/results/logs/run$1-$m.log)"
done
