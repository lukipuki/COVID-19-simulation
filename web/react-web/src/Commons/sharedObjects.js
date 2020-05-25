import React from 'react';

export const seriesInit = []; //set of date + country_shortname
export const SeriesContext = React.createContext(seriesInit);

export const availablePredictionsInit = []; // data from server - list
export const AvailablePredictionsContext = React.createContext(availablePredictionsInit);

export const selectedSeriesInit = []; // {country, prediction}
export const SelectedSeriesContext = React.createContext(selectedSeriesInit);

export const AXES_LINEAR = 1;
export const AXES_LOG = 2;
export const AXES_LOG_LOG = 3;

export const SCALING_ABSOLUTE = 1;
export const SCALING_PER_CAPITA = 2;
export const SCALING_SAME_PEAK = 3;

export const graphDetailsInit = { //options for graph
    axesType: AXES_LINEAR,
    dataScaling: SCALING_PER_CAPITA,
    isXAxisRelative: false
};
export const GraphDetailContext = React.createContext(graphDetailsInit);

export const locale = navigator.language;