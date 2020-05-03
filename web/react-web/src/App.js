import React, {Component} from 'react';
import './App.css';
import Sidebar from './Sidebar';
import {
    AvailablePredictionsContext,
    availablePredictionsInit,
    DataContext,
    dataInit,
    GraphDetailContext,
    graphDetailsInit,
    SelectionContext,
    selectionInit
} from "./sharedObjects";
import GraphWrapper from "./Graph";

class App extends Component {

    state = {
        selectionContext: selectionInit,
        availablePredictionsContext: availablePredictionsInit,
        dataContext: dataInit,
        graphDetailsContext: graphDetailsInit,
        sideBarHidden: false
    };

    toggleSidebar = () => {
        this.setState({
            sideBarHidden: !this.state.sideBarHidden
        })
    };

    setAvailablePredictions = (data) => {
        this.setState({
            availablePredictionsContext: data
        });

        //TODO consider auto-select when there is nothing selected
    };

    toggleSelection = (selection) => {
        const selections = this.state.selectionContext;
        const result = {...selections};
        if (result.hasOwnProperty(selection)) {
            delete result[selection]
        } else {
            result[selection] = true;
        }

        this.setState({
            selectionContext: result
        });

        if (!this.state.dataContext.hasOwnProperty(selection)) {
            this.fetchData(selection);
        }
    };

    setOptions = (options) => {
        this.setState({
            graphDetailsContext: options
        })
    };

    fetchData = (what) => {
        fetch(`/covid19/rest/${what}`, {cache: 'no-cache'})
            .then((response) => {
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error();
                }
            })
            .then((data) => {
                const newData = {...this.state.dataContext};
                newData[what] = data;
                this.setState({
                    dataContext: newData
                });
            })
            .catch(() => {});
    };

    componentDidMount() {
        fetch('/covid19/rest/predictions/list/', {cache: 'no-cache'})
            .then((response) => {
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error();
                }
            })
            .then(this.setAvailablePredictions)
            .catch(() => {});
    }

    render() {
        const {
            sideBarHidden
        } = this.state;

        const appClassName = `App ${sideBarHidden ? 'side-hidden' : 'side-visible'}`;

        return (
            <AvailablePredictionsContext.Provider value={{data: this.state.availablePredictionsContext, setData: this.setAvailablePredictions}}>
                <SelectionContext.Provider value={{selections: this.state.selectionContext, toggle: this.toggleSelection}}>
                    <DataContext.Provider value={this.state.dataContext}>
                        <GraphDetailContext.Provider value={{options: this.state.graphDetailsContext, setOptions: this.setOptions}}>
                            <div className={appClassName}>
                                <div className='sidebar'>
                                    <Sidebar />
                                </div>
                                <div className='content'>
                                    <GraphWrapper />
                                </div>
                                <img src={require('./assets/Hamburger_icon.svg')} className='side_switch' onClick={this.toggleSidebar} alt='Show/Hide graph'/>
                            </div>
                        </GraphDetailContext.Provider>
                    </DataContext.Provider>
                </SelectionContext.Provider>
            </AvailablePredictionsContext.Provider>
        );
    }
}

export default App;
