#!/bin/zsh -xe

declare -A short_names
short_names["US"]=USA
short_names["United Kingdom"]=UK

python3.7 -m venv --system-site-packages venv && source venv/bin/activate
pip install $1/
for country in Germany Iran Italy Spain "United Kingdom" US
do
  if [[ -z $short_names["${country}"] ]]; then
    covid_graphs.prepare_data $country
  else
    covid_graphs.prepare_data $country --short_name $short_names["${country}"]
  fi
done

deactivate && rm -rf venv
