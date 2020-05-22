import React, {PureComponent} from 'react';
import './App.css';
import Sidebar from './Sidebar';
import {
    AvailablePredictionsContext,
    availablePredictionsInit,
    GraphDetailContext,
    graphDetailsInit,
    SelectedSeriesContext,
    selectedSeriesInit,
    SeriesContext,
    seriesInit
} from "./Commons/sharedObjects";
import Content from "./Content";
import {api} from "./Commons/api";
import {ReactComponent as HamburgerIcon} from './assets/Hamburger_icon.svg';

class App extends PureComponent {

    state = {
        seriesContext: seriesInit,
        availablePredictionsContext: availablePredictionsInit,
        graphDetailsContext: graphDetailsInit,
        selectedSeriesContext: selectedSeriesInit,
        sideBarHidden: false
    };

    toggleSidebar = () => {
        this.setState({
            sideBarHidden: !this.state.sideBarHidden
        })
    };

    pendingRequests = new Set();
    fetchSeries = (country, prediction) => {
        const key = `${country}/${prediction}`;
        if (this.pendingRequests.has(key)) {
            return;
        }
        this.pendingRequests.add(key);
        if (prediction === null) {
            api.getCountryData(country)
                .then(countryData => {
                    const {
                        seriesContext,
                    } = this.state;

                    const result = [...seriesContext, countryData];
                    this.setState({
                        seriesContext: result
                    });
                })
                .catch(error => {
                    //TODO: handle this better
                    console.log(error);
                })
                .finally(() => {
                    this.pendingRequests.delete(key);
                });
        } else {
            api.getPredictionsByCountry(country)
                .then(predictions => {
                    const {
                        seriesContext,
                    } = this.state;

                    const result = seriesContext.concat(predictions);
                    this.setState({
                        seriesContext: result
                    });
                })
                .catch(error => {
                    //TODO: handle this better
                    console.log(error);
                })
                .finally(() => {
                    this.pendingRequests.delete(key);
                });
        }
    };

    setSelectedSeries = (series) => {
        this.setState({
            selectedSeriesContext: series
        });
    };

    setOptions = (options) => {
        this.setState({
            graphDetailsContext: options
        })
    };

    setAvailablePredictions = (predictions) => {
        this.setState({
            availablePredictionsContext: predictions
        })
    };

    componentDidMount() {
        api.getList()
            .then(this.setAvailablePredictions)
            .catch((error) => {
                //TODO: handle this better
                console.log(error);
            });
    }

    render() {
        const {
            sideBarHidden
        } = this.state;

        const appClassName = `App ${sideBarHidden ? 'side-hidden' : 'side-visible'}`;

        return (
            <AvailablePredictionsContext.Provider value={{data: this.state.availablePredictionsContext, setData: this.setAvailablePredictions}}>
                <SeriesContext.Provider value={{data: this.state.seriesContext, fetchSeries: this.fetchSeries}}>
                    <GraphDetailContext.Provider value={{options: this.state.graphDetailsContext, setOptions: this.setOptions}}>
                        <SelectedSeriesContext.Provider value={{data: this.state.selectedSeriesContext, setSelectedSeries: this.setSelectedSeries}}>
                            <div className={appClassName}>
                                <div className='sidebar'>
                                    <Sidebar />
                                </div>
                                <div className='content'>
                                    <Content />
                                </div>
                                <HamburgerIcon className='side_switch' onClick={this.toggleSidebar} title='Show/Hide graph'/>
                            </div>
                        </SelectedSeriesContext.Provider>
                    </GraphDetailContext.Provider>
                </SeriesContext.Provider>
            </AvailablePredictionsContext.Provider>
        );
    }
}

export default App;
