import React, {Component} from 'react';
import 'rc-slider/assets/index.css';
import {areSetsEqual} from "../../Commons/functions";
import Slider from "rc-slider";
import {locale} from "../../Commons/sharedObjects";

const optionsAxis = { month: 'numeric', day: 'numeric' };
const optionsLabel = { weekday: 'short', month: 'numeric', day: 'numeric' };

function tooltipFormatter(value) {
    return new Date(value).toLocaleDateString(locale, optionsLabel);
}

const MIN_MARK_WIDTH = 35;

const Handle = Slider.Handle;
const handle = (props) => {
    const { value, dragging, index, ...restProps } = props;
    return (
        <Handle value={value} {...restProps}>
            <div className={`tooltip${dragging ? ' active' : ''}`}>
                <div className='arrow'/>
                {tooltipFormatter(value)}
            </div>
        </Handle>
    );
};

class PredictionChanger extends Component {

    static defaultProps = {
        selectedSeries: null,
        predictions: null
    };

    timeout = null;

    state = {
        value: null,
        playing: false,
        marks: {},
        min: null,
        max: null
    };

    componentDidUpdate(prevProps, prevState, snapshot) {
        const {
            selectedSeries,
        } = this.props;

        const {
            selectedSeries: oldSelectedSeries,
        } = prevProps;

        const {
            value
        } = this.state;

        const {
            value: oldValue
        } = prevState;

        let updatePredictions = value !== oldValue;

        if (!updatePredictions) {
            if (selectedSeries !== oldSelectedSeries) {
                const oldCountries = this.getUsedCountries(oldSelectedSeries.data);
                const countries = this.getUsedCountries(selectedSeries.data);
                if (!areSetsEqual(oldCountries, countries)) {
                    this.updateMarks();
                    if (value !== null) {
                        //if we added country, we need to also add prediction
                        updatePredictions = true;
                    }
                }
            }
        }

        if (updatePredictions) {
            this.updatePredictions();
        }
    }

    getUsedCountries = (series) => {
        const usedCountries = new Set();
        //compute range and used countries for prediction selection
        series.forEach((one) => {
            usedCountries.add(one.country);
        });

        return usedCountries;
    };

    updatePredictions = () => {
        const {
            predictions,
            selectedSeries
        } = this.props;

        const {
            value,
        } = this.state;

        //remove old predictions
        const resultSeries = selectedSeries.data.filter((one) => one.prediction === null);
        const usedCountries = this.getUsedCountries(selectedSeries.data);

        //add new predictions
        predictions.data.forEach((prediction) => {
            const predictionDate = Date.parse(prediction.prediction_date);
            if (predictionDate === value &&
                usedCountries.has(prediction.country)) {
                resultSeries.push({
                    country: prediction.country,
                    prediction: prediction.prediction
                });
            }
        });
        selectedSeries.setSelectedSeries(resultSeries);
        this.scheduleNextPrediction();
    };

    updateMarks = () => {
        const {
            selectedSeries,
            predictions
        } = this.props;

        const usedCountries = this.getUsedCountries(selectedSeries.data);

        const marks = {};
        let minMark = null;
        let maxMark = null;
        let valueExist = false;
        predictions.data.forEach((prediction) => {
            if (usedCountries.has(prediction.country)) {
                const date = new Date(prediction.prediction_date);
                let label = date.toLocaleDateString(locale, optionsAxis);
                const time = date.getTime();

                minMark = minMark === null ? time : Math.min(minMark, time);
                maxMark = maxMark === null ? time : Math.max(maxMark, time);
                if (this.state.value === time) {
                    valueExist = true;
                }

                marks[time] = {
                    label,
                    time
                };

            }
        });

        // we need to remove labels that will overlap previous ones. Component do not have this feature.
        let lastRightOffset = -MIN_MARK_WIDTH;
        const element = document.getElementById('sliderWrapper');
        const marksCount = Object.keys(marks).length;
        if (element && marksCount > 2) {
            const markWidth = element.offsetWidth / (marksCount - 1);
            if (markWidth < MIN_MARK_WIDTH) {
                Object.keys(marks).sort((a, b) => a - b).forEach((key) => {
                    //avoid overlapping labels
                    const {time} = marks[key];
                    const leftOffset = (time - minMark) / (24 * 3600 * 1000) * markWidth - markWidth / 2;
                    if (leftOffset <= lastRightOffset) {
                        marks[time].label = null;
                    } else {
                        lastRightOffset = leftOffset + MIN_MARK_WIDTH;
                    }
                });
            }
        }


        this.setState({
            marks,
            min: minMark,
            max: maxMark,
            //autoselect latest (prediction)
            value: !valueExist ? maxMark : this.state.value
        });
    };

    onChange = (value) => {
        // workaround rc-slider bug when navigating by keyboard
        if (this.state.marks[value]) {
            this.setState({
                value: value
            });
        }
    };

    scheduleNextPrediction = () => {
        const {
            playing
        } = this.state;

        if (playing && !this.timeout) {
            this.timeout = setTimeout(() => {
                this.timeout = null;
                const values = Object.keys(this.state.marks).sort((a, b) => a - b);
                const valueIdx = values.indexOf(`${this.state.value}`);
                if (valueIdx > -1 && valueIdx < values.length - 1) {
                    this.onChange(parseInt(values[valueIdx + 1]));
                }
                if (valueIdx + 1 >= values.length) {
                    this.setState({
                        playing: false
                    });
                }
            }, 1000);
        } else if (!playing && this.timeout) {
            clearTimeout(this.timeout);
            this.timeout = null;
        }
    };

    toggleAnimation = () => {
        this.setState({
            playing: !this.state.playing
        }, this.scheduleNextPrediction);

        this.scheduleNextPrediction();
    };

    render() {
        const {
            marks,
            min,
            max,
            value,
            playing
        } = this.state;

        let buttonText = <div className='play'/>;
        if (this.state.playing) {
            buttonText = <div className='pause'/>;
        }

        const buttonDisabled = Object.keys(marks).length < 2;
        const buttonClassName = playing ? 'active' : '';

        return (
            <div className='sliderWrapper'>
                <button onClick={this.toggleAnimation} disabled={buttonDisabled} className={buttonClassName}>{buttonText}</button>
                <div id='sliderWrapper'>
                    <Slider
                        id='slider'
                        handle={handle}
                        marks={marks}
                        step={null}
                        onChange={this.onChange}
                        defaultValue={max}
                        value={value}
                        min={min}
                        max={max}
                        className='slider'
                    />
                </div>
            </div>
        )
    }
}

export default PredictionChanger;