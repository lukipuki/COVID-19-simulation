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
        Object.entries(predictions.data).forEach(([dateKey, prediction]) => {
            prediction.countries.forEach(country => {
                countries.add(country);
            });
        });
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

        return (
            <table>
                <thead>
                    <tr>
                        <th rowSpan={2}>Country<br/>(active cases)</th><th colSpan={predictionDates.length}>Predictions</th>
                    </tr>
                    <tr>
                        {predictionDates.map((value, index) => <th key={index}>{new Date(predictions.data[value].label).toLocaleDateString()}</th>)}
                    </tr>
                </thead>
                <tbody>{countryList}</tbody>
            </table>
        );
    }
}
export default Countries;