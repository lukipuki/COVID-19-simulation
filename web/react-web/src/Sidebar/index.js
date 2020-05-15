import React, {Component} from 'react';
import {
    GraphDetailContext, AXES_LINEAR, AXES_LOG, AXES_LOG_LOG, SCALING_PER_CAPITA,
    SCALING_ABSOLUTE, SCALING_SAME_PEAK
} from "../Commons/sharedObjects";
import CountriesWrapper from "./CountriesWrapper";
import ReactMarkdown from "react-markdown/with-html";
import {api} from "../Commons/api";

class Sidebar extends Component {
    state = {
        activeTab: 0,
        aboutMarkdown: ''
    };

    componentDidMount() {
        api.getAbout()
            .then((text) => {
                this.setState({
                    aboutMarkdown: text
                })
            })
            .catch((error) => {
                // TODO: handle better
                console.log(error);
            })
    }

    selectTab = (activeTab) => () => {
        this.setState({activeTab})
    };

    changeGraphDetail = (axesType, isXAxisRelative, dataScaling) => () => {
        const {setOptions} = this.context;
        if (!isXAxisRelative && axesType === AXES_LOG_LOG) {
            axesType = AXES_LINEAR;
        }
        setOptions({axesType, isXAxisRelative, dataScaling});
    };

    render() {
        return (
            <GraphDetailContext.Consumer>
                {graphDetailContext => {
                    const {isXAxisRelative, axesType, dataScaling} = graphDetailContext.options;
                    const {activeTab} = this.state;

                    return (
                        <>
                            <div className='buttons'>
                                <button className={activeTab === 0 ? 'active' : ''} onClick={this.selectTab(0)}>Results</button>
                                <button className={activeTab === 1 ? 'active' : ''} onClick={this.selectTab(1)}>About</button>
                            </div>
                            {activeTab === 0 &&
                                <>
                                    <fieldset>
                                        <legend>Show by:</legend>
                                        <div className='buttons'>
                                            <button onClick={this.changeGraphDetail(axesType, true, dataScaling)} className={isXAxisRelative ? 'active' : ''}>Day</button>
                                            <button onClick={this.changeGraphDetail(axesType, false, dataScaling)} className={!isXAxisRelative ? 'active' : ''}>Date</button>
                                        </div>
                                    </fieldset>
                                    <fieldset>
                                        <legend>Active cases:</legend>
                                        <div className='buttons'>
                                            <button
                                                onClick={this.changeGraphDetail(axesType, isXAxisRelative, SCALING_PER_CAPITA)}
                                                className={dataScaling === SCALING_PER_CAPITA ? 'active' : ''}>
                                                Per capita
                                            </button>
                                            <button
                                                onClick={this.changeGraphDetail(axesType, isXAxisRelative, SCALING_ABSOLUTE)}
                                                className={dataScaling === SCALING_ABSOLUTE ? 'active' : ''}>
                                                Absolute
                                            </button>
                                            <button
                                                onClick={this.changeGraphDetail(axesType, isXAxisRelative, SCALING_SAME_PEAK)}
                                                className={dataScaling === SCALING_SAME_PEAK ? 'active' : ''}>
                                                Same peak
                                            </button>
                                        </div>
                                    </fieldset>
                                    <fieldset>
                                        <legend>Axes adjustments:</legend>
                                        <div className='buttons'>
                                            <button
                                                onClick={this.changeGraphDetail(AXES_LINEAR, isXAxisRelative, dataScaling)}
                                                className={axesType === AXES_LINEAR ? 'active' : ''}>
                                                Linear
                                            </button>
                                            <button
                                                onClick={this.changeGraphDetail(AXES_LOG, isXAxisRelative, dataScaling)}
                                                className={axesType === AXES_LOG ? 'active' : ''}>
                                                Log Y
                                            </button>
                                            <button
                                                disabled={!isXAxisRelative}
                                                onClick={this.changeGraphDetail(AXES_LOG_LOG, isXAxisRelative, dataScaling)}
                                                className={axesType === AXES_LOG_LOG ? 'active' : ''}>
                                                Log XY
                                            </button>
                                        </div>
                                    </fieldset>
                                    <fieldset>
                                        <legend>Data & Predictions:</legend>
                                        <CountriesWrapper/>
                                    </fieldset>
                                    <h3>Legend</h3>
                                    <ul>
                                        <li>Solid/dotted line is prediction</li>
                                        <li>Star marks the culmination of the prediction</li>
                                        <li>Line with bullets is observed number of active cases</li>
                                        <li>Data available until the date of prediction is in <span className='lightgreen'>light green zone</span></li>
                                    </ul>
                                </>}
                            {activeTab === 1 &&
                            <>
                                <h1>COVID-19 predictions of Boďová and Kollár</h1>
                                <ReactMarkdown source={this.state.aboutMarkdown} escapeHtml={false} linkTarget='_blank' />
                            </>}
                        </>
                    )
                }}
            </GraphDetailContext.Consumer>
        );
    }
}

Sidebar.contextType = GraphDetailContext;

export default Sidebar;