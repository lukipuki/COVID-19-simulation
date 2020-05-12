import React, {Component} from 'react';
import GraphWrapper from "./Graph";
import PredictionChangerWrapper from "./PredictionChanger";

class Content extends Component {

    render() {
        return (
            <>
                <GraphWrapper/>
                <PredictionChangerWrapper/>
            </>
        )
    }
}

export default Content;