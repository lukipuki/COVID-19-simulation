import React, {Component} from 'react';
import Highcharts from 'highcharts'
import HighchartsReact from 'highcharts-react-official'
import {
    AXES_LINEAR, AXES_LOG, AXES_LOG_LOG, SCALING_ABSOLUTE, SCALING_PER_CAPITA,
    SCALING_SAME_PEAK
} from "../../Commons/sharedObjects";

const colors = ["#7cb5ec", "#434348", "#90ed7d", "#f7a35c", "#8085e9", "#f15c80", "#e4d354", "#2b908f", "#f45b5b", "#91e8e1"];

const predefinedOptions = {
    chart: {
        zoomType: 'x',
        colors,
    },
    title: {
        text: ''
    },
    subtitle: {
        text: document.ontouchstart === undefined ?
            'Click and drag in the plot area to zoom in' : 'Pinch the chart to zoom in'
    },
    tooltip: {
        shared: true,
        useHTML: true
    },
    xAxis: {
        type: 'linear',
        labels: {},
        title: {},
        crosshair: {
            width: 10,
            color: 'rgba(0, 0, 0, 0.1)'
        }
    },
    yAxis: {
        type: 'linear',
        title: {
            text: 'Active cases'
        },
        labels: {
            format: '{value}'
        }
    },
    legend: {
        enabled: true,
        useHTML: true,
        itemWidth: 300
    },
    plotOptions: {
        series: {
            animation: false
        },
        line: {
            marker: {
                symbol: 'circle'
            }
        }
    },

    series: []
};

function xaxis_text(x, isXAxisRelative) {
    if (isXAxisRelative) {
        return `Day ${x}`;
    } else {
        return new Date(x).toLocaleDateString();
    }
}

class Graph extends Component {

    static defaultProps = {
        options: {},
        series: []
    };

    getRelativeShift = (date, country) => {
        const {
            series
        } = this.props;
        for (let i = 0; i < series.length; i++) {
            const one = series[i];
            if (
                one.type !== 'prediction' &&
                one.short_name === country
            ) {
                const index = one.date_list.indexOf(date);
                return Math.max(0, index);
            }
        }
        return 0;
    };

    render() {
        const {
            series,
            options
        } = this.props;

        const {
            axesType,
            isXAxisRelative,
            dataScaling
        } = options.options;

        const finalOptions = {
            ...predefinedOptions
        };

        let countries = new Set();

        series.forEach(data => {
            countries.add(data.long_name);
        });
        countries = [...countries].sort();

        const resultSeries = [];

        series.forEach((one, index)=> {
            let maxXValue = null;
            let predictionXValue = null;
            let name = '';
            const zones = [];
            let dashStyle = 'line';
            //used for predictions and relative view, because predictions used to start later than the first data.
            let relativeShift = 0;

            if (one.type === 'prediction') {
                // calc solid and dashed part of prediction line
                if (isXAxisRelative) {
                    relativeShift = this.getRelativeShift(one.date_list[0], one.short_name);
                    maxXValue = one.date_list.indexOf(one.max_value_date) + 1 + relativeShift;
                    predictionXValue = one.date_list.indexOf(one.prediction_date) + 1 + relativeShift;
                } else {
                    maxXValue = Date.parse(one.max_value_date);
                    predictionXValue = Date.parse(one.prediction_date);
                }

                name = one.description.replace('%PREDICTION_DATE%', `, ${one.short_name}<br/>${new Date(one.prediction_date).toLocaleDateString()}`);

                zones.push({
                    value: predictionXValue,
                    dashStyle: 'line'
                });
                dashStyle = 'dash';
            } else {
                name = `Active cases for ${one.long_name}`;
            }

            let yRatio = 1.0;
            switch (dataScaling) {
                case SCALING_SAME_PEAK:
                    let maxValue = one.max_value;
                    if (one.type !== 'prediction') {
                        maxValue = Math.max(...one.values);
                    }
                    yRatio = maxValue * 100.0;

                    finalOptions.yAxis.title.text = 'Active cases %';
                    finalOptions.yAxis.labels.format = '{value}%';
                    break;
                case SCALING_PER_CAPITA:
                    yRatio = 1.0 / (one.population / 100000.0);
                    finalOptions.yAxis.title.text = 'Active cases per 100 000 citizens';
                    finalOptions.yAxis.labels.format = '{value}';
                    break;
                case SCALING_ABSOLUTE:
                default:
                    finalOptions.yAxis.title.text = 'Active cases';
                    finalOptions.yAxis.labels.format = '{value}';
                    break;
            }

            const lineData = one.date_list.map((date, index) => {
                const y = one.values[index] * yRatio;

                let x = null;
                if (isXAxisRelative) {
                    // relativeShift is 0 for non-predictions
                    x = index + 1 + relativeShift;
                } else {
                    x = Date.parse(date);
                }

                let marker = null;
                let enabled = null;

                if (x === maxXValue) {
                    enabled = true;
                    marker = {
                        symbol: 'triangle-down',
                            enabled: true,
                            radius: 8
                    };
                }

                if (x === predictionXValue) {
                    enabled = true;
                    marker = {
                        symbol: 'diamond',
                        enabled: true,
                        radius: 8
                    };
                }

                return {
                    enabled, x, y, marker
                };
            });

            resultSeries.push({
                type: 'line',
                dashStyle,
                name,
                marker: {
                    enabled: one.type !== 'prediction'
                },
                data: lineData,
                color: colors[resultSeries.length % colors.length],
                zones,
                zoneAxis: 'x'
            });
        });

        finalOptions.title = {
            text: `Active cases and prediction for ${countries.join(', ')}`
        };

        finalOptions.series = resultSeries;

        switch (axesType) {
            default:
            case AXES_LINEAR:
                finalOptions.xAxis.type = 'linear';
                finalOptions.yAxis.type = 'linear';
                break;
            case AXES_LOG:
                finalOptions.yAxis.type = 'logarithmic';
                finalOptions.xAxis.type = 'linear';
                break;
            case AXES_LOG_LOG:
                finalOptions.xAxis.type = 'logarithmic';
                finalOptions.yAxis.type = 'logarithmic';
                break;
        }

        if (isXAxisRelative) {
            finalOptions.xAxis.title.text = 'Day since relevant number of cases';

            finalOptions.xAxis.labels.formatter = function() {
                return this.value;
            };
        } else {
            finalOptions.xAxis.title.text = 'Date';

            finalOptions.xAxis.labels.formatter = function() {
                return Highcharts.dateFormat('%e %b', this.value);
            };
        }

        finalOptions.tooltip.formatter = function() {
            //https://api.highcharts.com/highcharts/tooltip.formatter
            if (this.points) {
                //shared tooltip, we need extract data from every series
                return this.points.reduce((s, point) => {
                    const name = point.series.name;
                    return `${s}<br/><strong>${name}:</strong> ${Math.round(point.y)}`;
                }, `<div style="text-align: center"><strong>${xaxis_text(this.x, isXAxisRelative)}</strong></div>`);
            } else {
                const name = this.point.series.name;
                return `<div style="text-align: center"><strong>${xaxis_text(this.x, isXAxisRelative)}</strong></div><strong>${name}:</strong> ${Math.round(this.point.y)}`;
            }
        };

        return <HighchartsReact
            highcharts={Highcharts}
            immutable={true}
            containerProps={{ style: { height: "100%" } }}
            className='graph'
            options={finalOptions}/>;
    }
}

export default Graph;
