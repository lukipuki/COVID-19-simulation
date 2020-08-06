#!/bin/zsh -xe

if [[ "${VIRTUAL_ENV:-}" == "" ]]
then
    echo "⚠️  Running outside of a virtual environment."
fi

declare -A short_names
short_names["United States"]=USA
short_names["United Kingdom"]=UK
short_names["New Zealand"]=NZ
short_names["South Korea"]=Korea

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
  Japan
  Latvia
  Lithuania
  Malaysia
  Monaco
  Morocco
  Netherlands
  "New Zealand"
  Poland
  Portugal
  Romania
  Russia
  Serbia
  Slovakia
  Slovenia
  "South Korea"
  Spain
  Switzerland
  Sweden
  Thailand
  Tunisia
  Turkey
  Ukraine
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
