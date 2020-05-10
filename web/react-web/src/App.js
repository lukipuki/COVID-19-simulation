import React, {Component} from 'react';
import './App.css';
import Sidebar from './Sidebar';
import {
    AvailablePredictionsContext,
    availablePredictionsInit,
    GraphDetailContext,
    graphDetailsInit,
    SeriesContext,
    seriesInit
} from "./Commons/sharedObjects";
import Content from "./Content";
import {api} from "./Commons/api";

class App extends Component {

    state = {
        seriesContext: seriesInit,
        availablePredictionsContext: availablePredictionsInit,
        graphDetailsContext: graphDetailsInit,
        sideBarHidden: false
    };

    toggleSidebar = () => {
        this.setState({
            sideBarHidden: !this.state.sideBarHidden
        })
    };

    setSeries = (series) => {
        this.setState({
            seriesContext: series
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
                <SeriesContext.Provider value={{data: this.state.seriesContext, setSeries: this.setSeries}}>
                    <GraphDetailContext.Provider value={{options: this.state.graphDetailsContext, setOptions: this.setOptions}}>
                        <div className={appClassName}>
                            <div className='sidebar'>
                                <Sidebar />
                            </div>
                            <div className='content'>
                                <Content />
                            </div>
                            <img src={require('./assets/Hamburger_icon.svg')} className='side_switch' onClick={this.toggleSidebar} alt='Show/Hide graph'/>
                        </div>
                    </GraphDetailContext.Provider>
                </SeriesContext.Provider>
            </AvailablePredictionsContext.Provider>
        );
    }
}

export default App;
