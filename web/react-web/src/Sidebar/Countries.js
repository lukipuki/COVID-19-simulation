import React, {Component} from 'react';
import {api} from "../Commons/api";

class Countries extends Component {

    static defaultProps = {
        predictions: {},
        series: {}
    };

    isCountryUsed = (country) => {
        const {
            data
        } = this.props.series;
        for (let i = 0; i < data.length; i++) {
            if (data[i].short_name === country) {
                return true;
            }
        }
        return false;
    };

    toggleItem = (country) => () => {
        const isUsed = this.isCountryUsed(country);
        const {
            data,
            setSeries
        } = this.props.series;

        if (isUsed) {
            const result = data.filter(one => one.short_name !== country);
            setSeries(result);
        } else {
            api.getCountryData(country)
                .then(countryData => {
                    const {
                        data,
                        setSeries
                    } = this.props.series;

                    const result = [...data, countryData];
                    setSeries(result);
                })
                .catch(error => {
                    //TODO: handle this better
                    console.log(error);
                });
            //prefetch all predictions to cache
            api.getPredictionsByCountry(country);
        }
    };

    render() {
        const {
            predictions
        } = this.props;

        let countries = new Set();
        predictions.data.forEach((prediction) => {
            countries.add(prediction.country);
        });
        countries = [...countries].sort();
        countries = countries.map((country) => {
            const className = this.isCountryUsed(country) ? 'active' : '';
            return (
                <button key={country} className={className} onClick={this.toggleItem(country)}>
                    {country}
                </button>
            );
        });

        return <div className='buttons'>{countries}</div>;
    }
}
export default Countries;