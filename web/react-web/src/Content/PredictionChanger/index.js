import React, {Component} from 'react';
import {AvailablePredictionsContext, SelectedSeriesContext} from "../../Commons/sharedObjects";
import PredictionChanger from "./PredictionChanger";


class PredictionChangerWrapper extends Component {

    render() {
        return (
            <AvailablePredictionsContext.Consumer>
                {predictions =>
                    <SelectedSeriesContext.Consumer>
                        {selectedSeriesContext => {
                            return <PredictionChanger selectedSeries={selectedSeriesContext}
                                                      predictions={predictions} />
                        }}
                    </SelectedSeriesContext.Consumer>
                }
            </AvailablePredictionsContext.Consumer>
        )
    }
}

export default PredictionChangerWrapper;