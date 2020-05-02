import React, {Component} from 'react';
import {DataContext, GraphDetailContext, SelectionContext} from "../sharedObjects";
import Graph from "./Graph";


class GraphWrapper extends Component {

    render() {
        return (
            <GraphDetailContext.Consumer>
                {graphDetailContext =>
                    <SelectionContext.Consumer>
                        {selectionContext =>
                            <DataContext.Consumer>
                                {dataContext => {
                                    const data = [];
                                    for (let key in selectionContext.selections) {
                                        if (dataContext.hasOwnProperty(key)) {
                                            data.push(dataContext[key]);
                                        }
                                    }

                                    return <Graph options={graphDetailContext} data={data}/>
                                }}
                            </DataContext.Consumer>
                        }
                    </SelectionContext.Consumer>
                }
            </GraphDetailContext.Consumer>
        )
    }
}

export default GraphWrapper;