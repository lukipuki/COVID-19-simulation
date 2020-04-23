import React, { Component } from 'react';
import {AvailablePredictionsContext, GraphDetailContext, MODE_LINEAR, MODE_LOG, MODE_LOG_LOG} from "../sharedObjects";
import Countries from "./Countries";

const options = { year: 'numeric', month: 'long', day: 'numeric' };

class Sidebar extends Component {
    state = {
        activeDateKey: null
    };

    selectDate = (activeDateKey) => () => {
        this.setState({activeDateKey})
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

                            for (let key in context.data) {
                                const item = context.data[key];
                                const date = new Date(Date.parse(item.label));
                                const className = `tab${this.state.activeDateKey === key ? ' active' : ''}`;

                                dates.push(<button key={key} className={className} onClick={this.selectDate(key)}>{date.toLocaleDateString(undefined, options)}</button>);
                            }

                            return (
                                <>
                                    <fieldset>
                                        <legend>Show by:</legend>
                                        <button onClick={this.changeGraphDetail(mode, true)} className={relative ? 'active' : ''}>By day</button>
                                        <button onClick={this.changeGraphDetail(mode, false)} className={!relative ? 'active' : ''}>By date</button>
                                    </fieldset>
                                    <fieldset>
                                        <legend>Axes adjustments:</legend>
                                        <button onClick={this.changeGraphDetail(MODE_LINEAR, relative)} className={mode === MODE_LINEAR ? 'active' : ''}>Linear</button>
                                        <button onClick={this.changeGraphDetail(MODE_LOG, relative)} className={mode === MODE_LOG ? 'active' : ''}>Log Y</button>
                                        <button disabled={!relative} onClick={this.changeGraphDetail(MODE_LOG_LOG, relative)} className={mode === MODE_LOG_LOG ? 'active' : ''}>Log XY</button>
                                    </fieldset>
                                    <fieldset className='countries'>
                                        <legend>Predictions by date:</legend>
                                        <div className='dates'>{dates}</div>
                                        <Countries selectedDateKey={this.state.activeDateKey}/>
                                    </fieldset>
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