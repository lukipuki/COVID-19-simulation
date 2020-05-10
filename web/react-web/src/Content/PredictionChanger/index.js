import React, {Component} from 'react';
import {GraphDetailContext, SeriesContext, AvailablePredictionsContext} from "../../Commons/sharedObjects";
import PredictionChanger from "./PredictionChanger";


class PredictionChangerWrapper extends Component {

    render() {
        return (
            <AvailablePredictionsContext.Consumer>
                {predictions =>
                    <SeriesContext.Consumer>
                        {seriesContext => {
                            return <PredictionChanger series={seriesContext}
                                                      predictions={predictions} />
                        }}
                    </SeriesContext.Consumer>
                }
            </AvailablePredictionsContext.Consumer>
        )
    }
}

export default PredictionChangerWrapper;