import React from 'react';
import {AvailablePredictionsContext, SelectedSeriesContext} from "../../Commons/sharedObjects";
import PredictionChanger from "./PredictionChanger";

const PredictionChangerWrapper = () => (
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
);

export default PredictionChangerWrapper;