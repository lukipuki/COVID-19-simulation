import React, {Component} from 'react';
import {AvailablePredictionsContext, SelectionContext} from "../sharedObjects";
import Countries from "./Countries";

class CountriesWrapper extends Component {

    render() {
        return (
            <AvailablePredictionsContext.Consumer>
                {predictionsContext =>
                    <SelectionContext.Consumer>
                        {selectionsContext => <div className='countries'><Countries predictions={predictionsContext} selections={selectionsContext}/></div>}
                    </SelectionContext.Consumer>
                }
            </AvailablePredictionsContext.Consumer>
        );
    }
}
export default CountriesWrapper;