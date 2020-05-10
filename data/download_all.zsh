#!/bin/zsh -xe

declare -A short_names
short_names["United States"]=USA
short_names["United Kingdom"]=UK
short_names["New Zealand"]=NZ
short_names["South Korea"]=Korea

python3 -m venv --system-site-packages venv && source venv/bin/activate
pip install $1/

countries=(
  Australia
  Austria
  Belgium
  Canada
  Chile
  Croatia
  Czechia
  Cyprus
  Estonia
  Finland
  France
  Georgia
  Germany
  Greece
  Hungary
  Iceland
  Iran
  Ireland
  Israel
  Italy
  Jordan
  Latvia
  Lithuania
  Malaysia
  Monaco
  Morocco
  Netherlands
  "New Zealand"
  Norway
  Poland
  Portugal
  Romania
  Russia
  Slovakia
  "South Korea"
  Spain
  Switzerland
  Sweden
  Thailand
  Tunisia
  Turkey
  Ukraine
  "United Kingdom"
  "United States"
)

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
