import React, {Component} from 'react';
import {GraphDetailContext, SelectedSeriesContext, SeriesContext} from "../../Commons/sharedObjects";
import Graph from "./Graph";


class GraphWrapper extends Component {

    render() {
        return (
            <GraphDetailContext.Consumer>
                {graphDetailContext =>
                    <SeriesContext.Consumer>
                        {seriesContext =>
                            <SelectedSeriesContext.Consumer>
                                {selectedSeriesContext => {
                                    let result = [];
                                    for (let i = 0; i < selectedSeriesContext.data.length; i++) {
                                        const selectedOne = selectedSeriesContext.data[i];
                                        const validItem = seriesContext.data.reduce((res, one) => {
                                            if (selectedOne.country === one.short_name) {
                                                if (selectedOne.prediction === null && one.type !== 'prediction') {
                                                    return one;
                                                }
                                                if (selectedOne.prediction === one.prediction_name) {
                                                    return one;
                                                }
                                            }
                                            return res;
                                        }, null);

                                        if (validItem === null) {
                                            // we have no data, let's fetch them
                                            // TODO: this is not best practice. Probably should be moved to
                                            // componentDidUpdate in Graph or another wrapper
                                            seriesContext.fetchSeries(selectedOne.country, selectedOne.prediction);
                                        } else {
                                            result.push(validItem);
                                        }
                                    }

                                    result = result.sort((a, b) => a.short_name.localeCompare(b.short_name));

                                    return <Graph options={graphDetailContext} series={result}/>;
                                }}
                            </SelectedSeriesContext.Consumer>
                        }
                    </SeriesContext.Consumer>
                }
            </GraphDetailContext.Consumer>
        )
    }
}

GraphWrapper.contextType = SeriesContext;

export default GraphWrapper;