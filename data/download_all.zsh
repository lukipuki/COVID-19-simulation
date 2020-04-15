#!/bin/zsh -xe

declare -A short_names
short_names["US"]=USA
short_names["United Kingdom"]=UK
short_names["New Zealand"]=NZ

python3.7 -m venv --system-site-packages venv && source venv/bin/activate
pip install $1/

#Korea Australia Canada 
countries=("United Kingdom" Austria Iceland Jordan Switzerland Croatia
  Germany Israel Italy Malaysia "New Zealand" Spain Belgium Chile Czechia Latvia
  Lithuania Netherlands Norway Portugal US)
for country in $countries
do
  echo $country
  if [[ -z $short_names["${country}"] ]]; then
    covid_graphs.prepare_data $country
  else
    covid_graphs.prepare_data $country --short_name $short_names["${country}"]
  fi
done

deactivate && rm -rf venv
