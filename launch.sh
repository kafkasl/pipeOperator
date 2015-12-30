#!/bin/bash

if [[ $# -ne 1 ]]; then

    echo "Usage: ./launch.sh INPUT_FILE"

else
    file=$1

    mkdir -p results
    rm -r results/*

    python operate_sequential.py $file > results/seq_out 2> results/seq_err

    for i in 2 3 4 6; do
        for j in 25000 50000 75000 100000 200000; do
            outfile="results/out_$j$i.txt"
            errfile="results/err_$j$i.txt"
            python operate_pipes.py $file $j $i > $outfile 2> $errfile
        done
    done
fi
