#!/bin/zsh -x

declare -A short_names
short_names["US"]=USA
short_names["United Kingdom"]=UK

#TODO: get rid of PYTHONPATH
export PYTHONPATH=../graphs
for country in France Germany Iran Italy Spain "United Kingdom" US
do
  if [[ -z $short_names["${country}"] ]]; then
    ./prepare_data.py $country
  else
    ./prepare_data.py $country --short_name $short_names["${country}"]
  fi
done
