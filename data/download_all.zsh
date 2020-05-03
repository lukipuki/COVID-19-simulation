#!/bin/zsh -xe

declare -A short_names
short_names["United States"]=USA
short_names["United Kingdom"]=UK
short_names["New Zealand"]=NZ
short_names["South Korea"]=Korea

python3 -m venv --system-site-packages venv && source venv/bin/activate
pip install $1/

countries=("United Kingdom" "South Korea" Austria Iceland Jordan Switzerland Croatia Australia
  Canada Germany Iran Israel Italy Malaysia "New Zealand" Spain Belgium Chile Czechia Latvia
  Lithuania Netherlands Norway Portugal France "United States")
for country in $countries
do
  if [[ -z $short_names["${country}"] ]]; then
    short_name=${country}
  else
    short_name=$short_names["${country}"]
  fi
  covid_graphs.prepare_data ${(p)country} --short_name ${short_name}
  covid_graphs.generate_predictions ${short_name}.data predictions
done

deactivate && rm -rf venv
