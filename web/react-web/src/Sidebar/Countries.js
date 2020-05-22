import React, {PureComponent} from 'react';

class Countries extends PureComponent {

    static defaultProps = {
        predictions: {},
        selectedSeries: {}
    };

    componentDidUpdate(prevProps, prevState, snapshot) {
        const {
            data: oldData
        } = prevProps.predictions;

        const {
            data
        } = this.props.predictions;

        if (data !== oldData && data.length > 0 && this.props.selectedSeries.data.length === 0) {
            //no series selected? Autoselect Slovakia or first country
            const country = data.reduce((currentValue, prediction) => {
                if (prediction.country === 'Slovakia') {
                    return 'Slovakia';
                }
                return currentValue;
            }, data[0].country);
            this.turnOnCountry(country)();
        }
    }

    isCountryUsed = (country) => {
        const {
            data
        } = this.props.selectedSeries;
        for (let i = 0; i < data.length; i++) {
            if (data[i].country === country) {
                return true;
            }
        }
        return false;
    };

    turnOnCountry = (country) => () => {
        const {
            data,
            setSelectedSeries
        } = this.props.selectedSeries;

        for (let i = 0; i < data.length; i++) {
            const item = data[i];
            if (item.country === country && item.prediction === null) {
                return;
            }
        }
        const result = [...data];
        result.push({
            country,
            prediction: null
        });
        setSelectedSeries(result);
    };

    turnOffCountry = (country) => () => {
        const {
            data,
            setSelectedSeries
        } = this.props.selectedSeries;

        const result = data.filter((item) => item.country !== country);
        setSelectedSeries(result);
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
            const isActive = this.isCountryUsed(country);
            const className = isActive ? 'active' : '';
            const onClick = isActive ? this.turnOffCountry(country) : this.turnOnCountry(country);
            return (
                <button key={country} className={className} onClick={onClick}>
                    {country}
                </button>
            );
        });

        return <div className='buttons'>{countries}</div>;
    }
}
export default Countries;