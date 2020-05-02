import React, {Component} from 'react';

class Countries extends Component {

    static defaultProps = {
        predictions: {},
        selections: []
    };

    toggleItem = (item) => () => {
        const {toggle} = this.props.selections;
        toggle(item);
    };

    render() {
        const {
            predictions,
            selections
        } = this.props;

        if (!predictions.data) {
            return null;
        }

        const countries = new Set();
        const predictionDates = Object.keys(predictions.data).sort();
        for (let dateKey in predictions.data) {
            const prediction = predictions.data[dateKey];
            prediction.countries.forEach(country => {
                countries.add(country);
            });
        }
        const countryList = [...countries].sort().map((country, index) => {
            const checks = predictionDates.map((prediction, i) => {
                const isAvailable = predictions.data[prediction].countries.indexOf(country) !== -1;
                if (!isAvailable) {
                    return <td key={i}/>
                }

                const key = `predictions/data/${prediction}/${country}`;
                const isSelected = selections.selections.hasOwnProperty(key);

                return <td key={i}><input type='checkbox' checked={isSelected ? 'checked' : ''} onChange={this.toggleItem(key)}/></td>
            });

            const countryKey = `data/${country}`;
            const className = selections.selections.hasOwnProperty(countryKey) ? 'active' : '';

            return <tr key={index}><td><button className={className} onClick={this.toggleItem(countryKey)}>{country}</button></td>{checks}</tr>
        });


        // if (!predictionsContext.data.hasOwnProperty(this.props.selectedDateKey)) {
        //     return null; //Loader
        // }
        // const predictionsToDate = predictionsContext.data[this.props.selectedDateKey];
        //
        // const countries = predictionsToDate.countries.map((country, i)=> {
        //         //a bit hacky to use part of api path as key
        //         const prediction = `${this.props.selectedDateKey}/${country}`;
        //         const active = selectionsContext.selections.hasOwnProperty(prediction);
        //         const className = `country${active ? ' active' : ''}`;
        //         return <button key={i} className={className} onClick={this.togglePrediction(prediction)}>{country}</button>
        //     }
        // );
        //
        // return <div className='buttons'>{countries}</div>;

        return <table>
            <thead>
                <tr>
                    <th rowSpan={2}>Country<br/>(active cases)</th><th colSpan={predictionDates.length}>Predictions</th>
                </tr>
                <tr>
                    {predictionDates.map((value, index) => <th key={index}>{new Date(Date.parse(predictions.data[value].label)).toLocaleDateString()}</th>)}
                </tr>
            </thead>
            <tbody>{countryList}</tbody>
        </table>;
    }
}
export default Countries;