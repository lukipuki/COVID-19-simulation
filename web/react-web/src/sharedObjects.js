import React from 'react';

export const selectionInit = {}; //set of date + country_shortname
export const SelectionContext = React.createContext(selectionInit);

export const availablePredictionsInit = null; // data from server - date + countries
export const AvailablePredictionsContext = React.createContext(availablePredictionsInit);

export const dataInit = {}; // cached data from server for each date + country
export const DataContext = React.createContext(dataInit);

export const MODE_LINEAR = 1;
export const MODE_LOG = 2;
export const MODE_LOG_LOG = 3;

export const graphDetailsInit = { //options for graph
    mode: MODE_LINEAR,
    relative: false
};
export const GraphDetailContext = React.createContext(graphDetailsInit);