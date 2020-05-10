import React, {Component} from 'react';
import {GraphDetailContext, SeriesContext} from "../../Commons/sharedObjects";
import Graph from "./Graph";


class GraphWrapper extends Component {

    render() {
        return (
            <GraphDetailContext.Consumer>
                {graphDetailContext =>
                    <SeriesContext.Consumer>
                        {seriesContext => {
                                return <Graph options={graphDetailContext} series={seriesContext.data}/>;
                            }
                        }
                    </SeriesContext.Consumer>
                }
            </GraphDetailContext.Consumer>
        )
    }
}

export default GraphWrapper;