import React, {Component} from 'react';
import {AvailablePredictionsContext, GraphDetailContext, MODE_LINEAR, MODE_LOG, MODE_LOG_LOG} from "../sharedObjects";
import CountriesWrapper from "./CountriesWrapper";

const options = { year: 'numeric', month: 'long', day: 'numeric' };

class Sidebar extends Component {
    state = {
        activeTab: 0
    };

    selectTab = (activeTab) => () => {
        this.setState({activeTab})
    };

    changeGraphDetail = (mode, relative) => () => {
        const {setOptions} = this.context;
        if (!relative && mode === MODE_LOG_LOG) {
            mode = MODE_LINEAR;
        }
        setOptions({mode, relative});
    };

    render() {
        return (
            <AvailablePredictionsContext.Consumer>
                {context =>
                    <GraphDetailContext.Consumer>
                        {graphDetailContext => {
                            const dates = [];
                            const {relative, mode} = graphDetailContext.options;
                            const {activeTab} = this.state;

                            for (let key in context.data) {
                                const item = context.data[key];
                                const date = new Date(Date.parse(item.label));
                                const className = `tab${this.state.activeDateKey === key ? ' active' : ''}`;

                                dates.push(<button key={key} className={className} onClick={this.selectTab(key)}>{date.toLocaleDateString(undefined, options)}</button>);
                            }

                            return (
                                <>
                                    <div className='buttons'>
                                        <button className={activeTab === 0 ? 'active' : ''} onClick={this.selectTab(0)}>About</button>
                                        <button className={activeTab === 1 ? 'active' : ''} onClick={this.selectTab(1)}>Results</button>
                                    </div>
                                    {activeTab === 0 &&
                                        <>
                                            <h1>COVID-19 predictions of Boďová and Kollár</h1>
                                            <p>Mathematicians Katarína Boďová and Richard Kollár predicted in March and April 2020
                                            the growth of active cases during COVID-19 pandemic. Their model suggests polynomial
                                            growth with exponential decay given by:</p>
                                            <ul>
                                                <li><em>N</em>(<em>t</em>) = (<em>A</em>/<em>T</em><sub><em>G</em></sub>) ⋅
                                                (<em>t</em>/<em>T</em><sub><em>G</em></sub>)<sup>α</sup> /
                                                e<sup><em>t</em>/<em>T</em><sub><em>G</em></sub></sup></li>
                                            </ul>
                                            <p>Where:</p>
                                            <ul><li><em>t</em> is time in days counted from a country-specific "day one"</li><li><em>N(t)</em> the number of active cases (cumulative positively tested minus recovered and deceased)</li><li><em>A</em>, <em>T<sub>G</sub></em> and <em>α</em> are country-specific parameters</li></ul>
                                            <p>They made two predictions, on March 30 (for 7 countries) and on April 12 (for 23
                                            countries), each based on data available until the day before. The first prediction
                                            assumed a common growth parameter <em>α</em> = 6.23.</p>
                                            <h3>References</h3>
                                            <ul>
                                                <li><a href="https://arxiv.org/abs/cond-mat/0505116">Polynomial growth in age-dependent branching processes with diverging reproductive number</a> by Alexei Vazquez</li>
                                                <li><a href="https://www.medrxiv.org/content/10.1101/2020.02.16.20023820v2.full.pdf">Fractal kinetics of COVID-19 pandemic</a> by Robert Ziff and Anna Ziff</li>
                                                <li>Unpublished manuscript by Katarína Boďová and Richard Kollár</li>
                                                <li>March 30 predictions: <a href="https://www.facebook.com/permalink.php?story_fbid=10113020662000793&amp;id=2247644">Facebook post</a></li>
                                                <li>April 13 predictions: Personal communication</li>
                                            </ul>
                                        </>}
                                    {activeTab === 1 &&
                                        <>
                                            <h3>Results</h3>
                                            <fieldset>
                                                <legend>Show by:</legend>
                                                <div className='buttons'>
                                                    <button onClick={this.changeGraphDetail(mode, true)} className={relative ? 'active' : ''}>Day</button>
                                                    <button onClick={this.changeGraphDetail(mode, false)} className={!relative ? 'active' : ''}>Date</button>
                                                </div>
                                            </fieldset>
                                            <fieldset>
                                                <legend>Axes adjustments:</legend>
                                                <div className='buttons'>
                                                    <button onClick={this.changeGraphDetail(MODE_LINEAR, relative)} className={mode === MODE_LINEAR ? 'active' : ''}>Linear</button>
                                                    <button onClick={this.changeGraphDetail(MODE_LOG, relative)} className={mode === MODE_LOG ? 'active' : ''}>Log Y</button>
                                                    <button disabled={!relative} onClick={this.changeGraphDetail(MODE_LOG_LOG, relative)} className={mode === MODE_LOG_LOG ? 'active' : ''}>Log XY</button>
                                                </div>
                                            </fieldset>
                                            <fieldset>
                                                <legend>Data & Predictions:</legend>
                                                <CountriesWrapper/>
                                            </fieldset>
                                            <h3>Legend</h3>
                                            <ul>
                                                <li>Solid line is prediction</li>
                                                <li>Dashed line marks the culmination of the prediction</li>
                                                <li>Data available until the date of prediction is in color zones</li>
                                            </ul>
                                        </>}
                                </>
                            )
                        }}
                    </GraphDetailContext.Consumer>
                }
            </AvailablePredictionsContext.Consumer>
        );
    }
}

Sidebar.contextType = GraphDetailContext;

export default Sidebar;