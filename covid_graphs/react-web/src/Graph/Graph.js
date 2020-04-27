import React, {Component} from 'react';
import Highcharts from 'highcharts'
import HighchartsReact from 'highcharts-react-official'
import {MODE_LINEAR, MODE_LOG, MODE_LOG_LOG} from "../sharedObjects";
import {renderMath} from "./mathjax";

const colors = ["#7cb5ec", "#434348", "#90ed7d", "#f7a35c", "#8085e9", "#f15c80", "#e4d354", "#2b908f", "#f45b5b", "#91e8e1"];
const bandColors = [
    'rgba(139, 188, 33, 0.2)',
    'rgba(242, 143, 67, 0.2)',
    'rgba(73, 41, 112, 0.2)',
    'rgba(47, 126, 216, 0.2)',
    'rgba(13, 35, 58, 0.2)',
    'rgba(145, 0, 0, 0.2)',
    'rgba(26, 173, 206, 0.2)',
    'rgba(119, 161, 229, 0.2)',
    'rgba(196, 37, 37, 0.2)',
    'rgba(166, 201, 106, 0.2)'
];
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
        // shared: true
    },
    xAxis: {
        type: 'linear',
        labels: {},
        title: {}
    },
    yAxis: {
        type: 'linear',
        title: {
            text: 'Active cases'
        },
    },
    legend: {
        enabled: true,
        labelFormatter: function() {
            if (this.options.id) {
                renderMath(this.options.id);
            }

            return this.name;
        },
        useHTML: true,
        // align: 'right',
        // verticalAlign: 'middle',
        // layout: 'vertical',
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
        let xValues = [];

        data.forEach(data => {
            countries.add(data.long_name);
            xValues.concat(data.date_list);
        });
        countries = [...countries].sort();
        xValues = [...new Set(xValues)].sort();

        const series = [];
        const xLines = [];
        let predictionEnds = [];

        data.forEach((data, index)=> {
            const tmp = data.date_list.map((x, index) => {
                const y = data.values[index];
                if (relative) {
                    return [index + 1, y];
                }

                return [Date.parse(x), y];
            });

            if (data.type === 'prediction') {
                let value = Date.parse(data.max_value_date);
                if (relative) {
                    value = data.date_list.indexOf(data.max_value_date) + 1;
                }

                xLines.push(
                    {
                        dashStyle: 'dash',
                        value,
                        width: 2,
                        zIndex: 1,
                        color: colors[series.length % colors.length]
                    }
                );
            }

            let id = null;
            let name = '';
            if (data.type === 'prediction') {
                id = `legend-${data.date_name}/${data.short_name}`;
                name = `Prediction for ${data.long_name} ${new Date(Date.parse(data.date)).toLocaleDateString()}<br/><span id="${id}" style="display: inline-block; height: 60px; visibility: hidden">$${data.description}$</span>`

                if (relative) {
                    predictionEnds.push(xValues.indexOf(data.date) + 1);
                } else {
                    predictionEnds.push(Date.parse(data.date));
                }
            } else {
                name = `Active cases for ${data.long_name}`
            }

            series.push({
                type: 'line',
                name,
                id,
                marker: {
                    enabled: data.type !== 'prediction'
                },
                data: tmp,
                color: colors[series.length % colors.length]
            });
        });

        finalOptions.title = {
            text: `Active cases and prediction for ${countries.join(', ')}`
        };

        predictionEnds = [...new Set(predictionEnds)].sort().reverse();
        finalOptions.series = series;
        finalOptions.xAxis.plotLines = xLines;
        finalOptions.xAxis.plotBands = predictionEnds.map(
            (value, index)=> ({
                //color: 'orange',
                from: 0,
                to: value,
                color: bandColors[index % bandColors.length]
            })
        );

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
                        const name = point.series.name.split('<br/>')[0];
                        return `${s}<br/><strong>${name}:</strong> ${Math.round(point.y)}`;
                    }, `<strong>Day ${this.x}</strong>`);
                } else {
                    const name = this.point.series.name.split('<br/>')[0];
                    return `<strong>Day ${this.x}</strong><br/><strong>${name}:</strong> ${Math.round(this.point.y)}`;
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
                        const name = point.series.name.split('<br/>')[0];
                        return `${s}<br/><strong>${name}:</strong> ${Math.round(point.y)}`;
                    }, `<strong>${date.toLocaleDateString()}</strong>`);
                } else {
                    const date = new Date(this.x);
                    const name = this.point.series.name.split('<br/>')[0];
                    return `<strong>${date.toLocaleDateString()}</strong><br/><strong>${name}:</strong> ${Math.round(this.point.y)}`;
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