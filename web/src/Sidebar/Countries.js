import React, { Component } from 'react';
import {AvailablePredictionsContext, SelectionContext} from "../sharedObjects";

class Countries extends Component {

    static defaultProps = {
        selectedDateKey: null
    };

    togglePrediction = (prediction) => () => {
        const {toggle} = this.context;
        toggle(prediction);
    };

    render() {
        return (
            <AvailablePredictionsContext.Consumer>
                {predictionsContext =>
                    <SelectionContext.Consumer>
                        {selectionsContext => {
                                if (!predictionsContext.data.hasOwnProperty(this.props.selectedDateKey)) {
                                    return null; //Loader
                                }
                                const predictionsToDate = predictionsContext.data[this.props.selectedDateKey];

                                const countries = predictionsToDate.countries.map((country, i)=> {
                                        //a bit hacky to use part of api path as key
                                        const prediction = `${this.props.selectedDateKey}/${country}`;
                                        const active = selectionsContext.selections.hasOwnProperty(prediction);
                                        const className = `country${active ? ' active' : ''}`;
                                        return <button key={i} className={className} onClick={this.togglePrediction(prediction)}>{country}</button>
                                    }
                                );

                                return <div className='countries'>{countries}</div>;
                            }
                        }
                    </SelectionContext.Consumer>
                }
            </AvailablePredictionsContext.Consumer>
        );
    }
}
Countries.contextType = SelectionContext;

export default Countries;