import React, {Component} from 'react';
import {GraphDetailContext, AXES_LINEAR, AXES_LOG, AXES_LOG_LOG} from "../Commons/sharedObjects";
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

    changeGraphDetail = (axesType, isXAxisRelative) => () => {
        const {setOptions} = this.context;
        if (!isXAxisRelative && axesType === AXES_LOG_LOG) {
            axesType = AXES_LINEAR;
        }
        setOptions({axesType, isXAxisRelative});
    };

    render() {
        return (
            <GraphDetailContext.Consumer>
                {graphDetailContext => {
                    const {isXAxisRelative, axesType} = graphDetailContext.options;
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
                                            <button onClick={this.changeGraphDetail(axesType, true)} className={isXAxisRelative ? 'active' : ''}>Day</button>
                                            <button onClick={this.changeGraphDetail(axesType, false)} className={!isXAxisRelative ? 'active' : ''}>Date</button>
                                        </div>
                                    </fieldset>
                                    <fieldset>
                                        <legend>Axes adjustments:</legend>
                                        <div className='buttons'>
                                            <button onClick={this.changeGraphDetail(AXES_LINEAR, isXAxisRelative)} className={axesType === AXES_LINEAR ? 'active' : ''}>Linear</button>
                                            <button onClick={this.changeGraphDetail(AXES_LOG, isXAxisRelative)} className={axesType === AXES_LOG ? 'active' : ''}>Log Y</button>
                                            <button disabled={!isXAxisRelative} onClick={this.changeGraphDetail(AXES_LOG_LOG, isXAxisRelative)} className={axesType === AXES_LOG_LOG ? 'active' : ''}>Log XY</button>
                                        </div>
                                    </fieldset>
                                    <fieldset>
                                        <legend>Data & Predictions:</legend>
                                        <CountriesWrapper/>
                                    </fieldset>
                                    <h3>Legend</h3>
                                    <ul>
                                        <li>Triangle marks the culmination of the prediction</li>
                                        <li>Diamond marks the date when predction was made</li>
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