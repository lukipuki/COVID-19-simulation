import React from 'react';
import {AvailablePredictionsContext, SelectedSeriesContext} from "../Commons/sharedObjects";
import Countries from "./Countries";

const CountriesWrapper = () => (
    <AvailablePredictionsContext.Consumer>
        {predictionsContext =>
            <SelectedSeriesContext.Consumer>
                {selectedSeriesContext =>
                    <div className='countries'><Countries predictions={predictionsContext} selectedSeries={selectedSeriesContext}/></div>
                }
            </SelectedSeriesContext.Consumer>
        }
    </AvailablePredictionsContext.Consumer>
);

export default CountriesWrapper;