#! /bin/bash

for d in `find . -mindepth 1 -maxdepth 1 -type d`; do
    cd $d
    pwd
    ./run_example.sh
    cd ..
done
