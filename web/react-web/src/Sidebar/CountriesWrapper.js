import React, {Component} from 'react';
import {AvailablePredictionsContext, SeriesContext} from "../Commons/sharedObjects";
import Countries from "./Countries";

class CountriesWrapper extends Component {

    render() {
        return (
            <AvailablePredictionsContext.Consumer>
                {predictionsContext =>
                    <SeriesContext.Consumer>
                        {seriesContext => <div className='countries'><Countries predictions={predictionsContext} series={seriesContext}/></div>}
                    </SeriesContext.Consumer>
                }
            </AvailablePredictionsContext.Consumer>
        );
    }
}
export default CountriesWrapper;