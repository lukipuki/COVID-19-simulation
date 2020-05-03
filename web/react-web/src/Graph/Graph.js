import React, {Component} from 'react';
import Highcharts from 'highcharts'
import HighchartsReact from 'highcharts-react-official'
import {MODE_LINEAR, MODE_LOG, MODE_LOG_LOG} from "../sharedObjects";

const colors = ["#7cb5ec", "#434348", "#90ed7d", "#f7a35c", "#8085e9", "#f15c80", "#e4d354", "#2b908f", "#f45b5b", "#91e8e1"];

const predefinedOptions = {
    chart: {
        zoomType: 'x',
        colors,
    },
    title: {
        text: 'USD to EUR exchange rate over time'
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
        }
    },

    series: []
};

class Graph extends Component {

    static defaultProps = {
        options: {},
        data: []
    };

    render() {
        const {
            data,
            options
        } = this.props;

        const {
            mode,
            relative,
        } = options.options;

        const finalOptions = {
            ...predefinedOptions
        };

        let countries = new Set();

        data.forEach(data => {
            countries.add(data.long_name);
        });
        countries = [...countries].sort();

        const series = [];

        data.forEach((data, index)=> {
            let maxXValue = null;
            let predictionXValue = null;
            let name = '';
            const zones = [];
            let dashStyle = 'line';

            if (data.type === 'prediction') {
                if (relative) {
                    maxXValue = data.date_list.indexOf(data.max_value_date) + 1;
                    predictionXValue = data.date_list.indexOf(data.prediction_date) + 1;
                } else {
                    maxXValue = Date.parse(data.max_value_date);
                    predictionXValue = Date.parse(data.prediction_date);
                }

                name = data.description.replace('%PREDICTION_DATE%', `<br/>${new Date(Date.parse(data.prediction_date)).toLocaleDateString()}`);

                zones.push({
                    value: predictionXValue,
                    dashStyle: 'line'
                });
                dashStyle = 'dash';
            } else {
                name = `Active cases for ${data.long_name}`;
            }


            const lineData = data.date_list.map((date, index) => {
                const y = data.values[index];

                let x = null;
                if (relative) {
                    x = index + 1;
                } else {
                    x = Date.parse(date);
                }

                if (x === maxXValue) {
                    return {
                        enabled: true,
                        x,
                        y,
                        marker: {
                            symbol: 'triangle-down',
                            enabled: true,
                            radius: 8
                        }
                    }
                }

                if (x === predictionXValue) {
                    return {
                        enabled: true,
                        x,
                        y,
                        marker: {
                            symbol: 'diamond',
                            enabled: true,
                            radius: 8
                        }
                    }
                }

                return [x, y];
            });

            series.push({
                type: 'line',
                dashStyle,
                name,
                marker: {
                    enabled: data.type !== 'prediction'
                },
                data: lineData,
                color: colors[series.length % colors.length],
                zones,
                zoneAxis: 'x'
            });
        });

        finalOptions.title = {
            text: `Active cases and prediction for ${countries.join(', ')}`
        };

        finalOptions.series = series;

        switch (mode) {
            default:
            case MODE_LINEAR:
                finalOptions.xAxis.type = 'linear';
                finalOptions.yAxis.type = 'linear';
                break;
            case MODE_LOG:
                finalOptions.yAxis.type = 'logarithmic';
                finalOptions.xAxis.type = 'linear';
                break;
            case MODE_LOG_LOG:
                finalOptions.xAxis.type = 'logarithmic';
                finalOptions.yAxis.type = 'logarithmic';
                break;
        }

        if (relative) {
            finalOptions.tooltip.formatter = function() {
                if (this.points) {
                    return this.points.reduce((s, point) => {
                        const name = point.series.name;
                        return `${s}<br/><strong>${name}:</strong> ${Math.round(point.y)}`;
                    }, `<div style="text-align: center"><strong>Day ${this.x}</strong></div>`);
                } else {
                    const name = this.point.series.name;
                    return `<div style="text-align: center"><strong>Day ${this.x}</strong></div><br/><strong>${name}:</strong> ${Math.round(this.point.y)}`;
                }
            };

            finalOptions.xAxis.labels.formatter = function() {
                return this.value;
            };

            finalOptions.xAxis.title.text = 'Day since relevant number of cases';
        } else {
            finalOptions.tooltip.formatter = function() {
                if (this.points) {
                    const date = new Date(this.x);
                    return this.points.reduce((s, point) => {
                        const name = point.series.name;
                        return `${s}<br/><strong>${name}:</strong> ${Math.round(point.y)}`;
                    }, `<div style="text-align: center"><strong>${date.toLocaleDateString()}</strong></div>`);
                } else {
                    const date = new Date(this.x);
                    const name = this.point.series.name;
                    return `<div style="text-align: center"><strong>${date.toLocaleDateString()}</strong></div><strong>${name}:</strong> ${Math.round(this.point.y)}`;
                }
            };

            finalOptions.xAxis.labels.formatter = function() {
                return Highcharts.dateFormat('%e %b', this.value);
            };

            finalOptions.xAxis.title.text = 'Date';
        }

        return <HighchartsReact
            highcharts={Highcharts}
            immutable={true}
            containerProps={{ style: { height: "100%" } }}
            options={finalOptions}/>;
    }
}

export default Graph;