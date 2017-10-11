#!/bin/bash

for id in `cut -f4 $1 | sed -e 's/-/:::/g' | sort -t: -k1,1 -k2,2n | sed -e 's/:::/-/g' | uniq`;
do
grep $id $1
done