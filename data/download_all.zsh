#!/bin/zsh -xe

declare -A short_names
short_names["United States"]=USA
short_names["United Kingdom"]=UK
short_names["New Zealand"]=NZ

python3.7 -m venv --system-site-packages venv && source venv/bin/activate
pip install $1/

countries=("United Kingdom" Korea Austria Iceland Jordan Switzerland Croatia Australia Canada
  Germany Israel Italy Malaysia "New Zealand" Spain Belgium Chile Czechia Latvia
  Lithuania Netherlands Norway Portugal US)
for country in $countries
do
  if [[ -z $short_names[${(p)country}] ]]; then
    covid_graphs.prepare_data ${(p)country}
  else
    covid_graphs.prepare_data ${(p)country} --short_name $short_names[${(p)country}]
  fi
done

deactivate && rm -rf venv
