#!/bin/bash


declare -i sum
sum=0
for cntr in {1..10000000} ; do
    sum=$((sum+1))
done

echo "bash_loop.sh done, sum = $sum"

exit 0
