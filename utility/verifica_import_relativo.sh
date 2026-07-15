#!/usr/bin/env bash
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

RED='\033[0;31m'

pendencias=$(grep -rnw "from src" "src")
if [ "$pendencias" ] ;
then
   echo -e "${RED} Tem pendencias de import relativo..."
   echo $pendencias
   exit 1
fi
exit 0
