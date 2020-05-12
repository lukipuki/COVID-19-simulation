import React, {Component} from 'react';
import 'rc-slider/assets/index.css';
import 'rc-tooltip/assets/bootstrap.css';
import {api} from "../../Commons/api";
import {isSetsEqual} from "../../Commons/functions";
import Slider, {createSliderWithTooltip} from "rc-slider";

const optionsAxis = { month: 'numeric', day: 'numeric' };
const optionsLabel = { weekday: 'short', month: 'numeric', day: 'numeric' };

function tooltipFormatter(value) {
    return new Date(value).toLocaleDateString(undefined, optionsLabel);
}

const SliderWithTooltip = createSliderWithTooltip(Slider);

const MIN_MARK_WIDTH = 30;

class PredictionChanger extends Component {

    static defaultProps = {
        series: null,
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
            series,
        } = this.props;

        const {
            series: oldSeries,
        } = prevProps;

        const {
            value
        } = this.state;

        const {
            value: oldValue
        } = prevState;

        let updatePredictions = value !== oldValue;

        if (!updatePredictions) {
            if (series !== oldSeries) {
                const oldCountries = this.getUsedCountries(oldSeries.data);
                const countries = this.getUsedCountries(series.data);
                if (!isSetsEqual(oldCountries, countries)) {
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
            usedCountries.add(one.short_name);
        });

        return usedCountries;
    };

    updatePredictions = () => {
        const {
            predictions,
            series
        } = this.props;

        const {
            value,
        } = this.state;

        //remove old predictions
        const resultSeries = series.data.filter((one) => one.type !== 'prediction');

        series.setSeries(resultSeries);
        const usedCountries = this.getUsedCountries(series.data);

        //add new predictions
        const promises = [];
        predictions.data.forEach((prediction) => {
            const predictionDate = Date.parse(prediction.prediction_date);
            if (predictionDate === value &&
                usedCountries.has(prediction.country)) {
                promises.push(api.getPrediction(prediction.prediction, prediction.country)
                    .then((prediction) => {
                        const {
                            data,
                            setSeries
                        } = this.props.series;

                        const result = [...data, prediction];
                        setSeries(result);
                    })
                    .catch(error => {
                        //TODO: handle this better
                        console.log('error', error);
                    }));
            }
        });

        Promise.all(promises).finally(this.scheduleNextPrediction);
    };

    updateMarks = () => {
        const {
            series,
            predictions
        } = this.props;

        // let xValues = new Set();
        // //compute range and used countries for prediction selection
        // series.data.forEach((one) => {
        //     one.date_list.forEach(date => {
        //         xValues.add(Date.parse(date));
        //     });
        // });
        // xValues = [...xValues].sort();

        const usedCountries = this.getUsedCountries(series.data);

        const marks = {};
        let minMark = null;
        let maxMark = null;
        let valueExist = false;
        predictions.data.forEach((prediction) => {
            if (usedCountries.has(prediction.country)) {
                const date = new Date(prediction.prediction_date);
                let label = date.toLocaleDateString(undefined, optionsAxis);
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

        let lastRightOffset = -MIN_MARK_WIDTH;
        const element = document.getElementById('sliderWrapper');
        const marksCount = Object.keys(marks).length;
        if (element && marksCount > 2) {
            const markWidth = element.offsetWidth / (marksCount - 1);
            if (markWidth < MIN_MARK_WIDTH) {
                Object.keys(marks).sort().forEach((key) => {
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
            //autoselect first mark (prediction)
            value: !valueExist ? minMark : this.state.value
        });
    };

    onChange = (value) => {
        this.setState({
            value
        });
    };

    scheduleNextPrediction = () => {
        const {
            playing
        } = this.state;

        if (playing && !this.timeout) {
            this.timeout = setTimeout(() => {
                this.timeout = null;
                const values = Object.keys(this.state.marks).sort();
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
                    <SliderWithTooltip
                        id='slider'
                        tipProps={{visible: Object.keys(marks).length !== 0}}
                        tipFormatter={tooltipFormatter}
                        marks={marks}
                        step={null}
                        onChange={this.onChange}
                        defaultValue={min}
                        value={value}
                        min={min}
                        max={max}
                        className='slider'
                        trackStyle={{ backgroundColor: 'orange' }}
                        dotStyle={{ borderColor: 'linen' }}
                        activeDotStyle={{ borderColor: 'orange' }}
                        handleStyle={{ backgroundColor: 'linen', borderColor: 'orange' }}
                        railStyle={{ backgroundColor: 'linen' }}
                    />
                </div>
            </div>
        )
    }
}

export default PredictionChanger;