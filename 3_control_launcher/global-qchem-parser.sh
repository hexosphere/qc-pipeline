#!/usr/bin/env bash

module purge
module load Python/3.6.6-foss-2018b

for f in $(find . -maxdepth 1 -type d \( -not -iname "Tex" -not -iname "old" \)); do
        printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' '*'
        echo " "
        echo "generating files for molecule $f..."
        pushd $f || echo "$f not a folder to enter into. Skipping"; continue
        ln -s ../qchem-parser.py ./
        input="$f.out"
        python qchem-parser.py $input
        sed -i -e "s/0.000E+00/0.0/g" *_momdip.tex
        cp *.tex ../Tex/
        echo -ne "generating files for molecule $f... DONE"
        echo " "
        popd || popd || echo "Something gone wrong going back to parent folder. Exiting"; exit
done



