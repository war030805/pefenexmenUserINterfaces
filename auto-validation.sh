#!/bin/sh
#set echo off
echo Running auto-validation \(v6.1\)...

python3 ./auto-validation/_syntax-validatie/syntax-validator.py

python3 ./auto-validation/_conventies-validatie/conventions-validator.py

mkdir -p "goed"

mkdir -p "fout"

for file in *.txt; do
    # Controleer of het bestand (niet directory) is en "OK" in de bestandsnaam staat
    if [[ -f "$file" ]]; then
        if [[ "$file" == *OK* ]]; then
            # Verplaats naar 'goed' als 'OK' in de bestandsnaam staat
            veranderdefile=$(echo "$file" | sed 's/_OK//g')
            if [[ -f fout/$veranderdefile ]]; then
                rm fout/$veranderdefile
            fi
            mv "$file" goed/
        else
            # Verplaats naar 'fout' als 'OK' niet in de bestandsnaam staat
            for file2 in ./goed/*; do
              veranderdefile=$(echo "$file2" | sed 's/_OK//g')
#              echo "./goed/$file"
#              echo "$veranderdefile"
              if [ "./goed/$file" == "$veranderdefile" ]; then
                  rm "$file2"
              fi
              done
            mv "$file" fout/

        fi
    fi
done




    # Functie om bestanden te markeren voor verwijdering




