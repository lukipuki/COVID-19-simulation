#!/bin/zsh
#
declare -A short_names
short_names["France"]=France
short_names["Germany"]=Germany
short_names["Iran"]=Iran
short_names["Italy"]=Italy
short_names["Spain"]=Spain
short_names["US"]=USA
short_names["United Kingdom"]=UK

for country in France Germany Iran Italy Spain "United Kingdom" US
do
  ./prepare_data.py $country
  mv data.yaml data-$short_names["$country"].yaml
done
