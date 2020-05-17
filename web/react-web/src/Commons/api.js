function doRequest(type = 'GET', path, data = null, query = null) {
    let params = '';
    if (query !== null) {
        params = '?' + Object.keys(query).map(k => `${encodeURIComponent(k)}=${encodeURIComponent(query[k])}`).join('&');
    }

    const uri = `${path}${params}`;
    const xhr = new XMLHttpRequest();
    xhr.open(type, uri, true);

    if (!(data instanceof FormData)) {
        xhr.setRequestHeader('Content-Type', 'application/json');
    }

    xhr.timeout = 60*1000;

    const promise = new Promise((resolve, reject) => {
        xhr.addEventListener('load', (event) => {
            if (xhr.status < 200 || xhr.status >= 400) {
                reject(new Error(xhr.responseText, xhr.status));
            } else {
                let response = null;
                try {
                    response = JSON.parse(xhr.response);
                    resolve(response);
                } catch (e) {
                    reject(new Error('Invalid data'));
                }
            }
        });
        xhr.addEventListener('error', (e) => {
            reject(new Error('connection error'));
        });
        xhr.addEventListener('abort', (e) => {
            reject(new Error('request aborted'));
        });
        xhr.addEventListener('timeout', (e) => {
            reject(new Error('request timeout'));
        });
        try {
            xhr.send(data);
        } catch (e) {
            reject(e);
        }
    });

    promise.abort = xhr.abort;

    return promise;
}

export const api = {
    getList: () => {
        return doRequest('GET', '/covid19/rest/predictions/list');
    },
    getCustom: (what) => {
        return doRequest('GET', `/covid19/rest/${what}`);
    },
    getCountryData: (country) => {
        return doRequest('GET', `/covid19/rest/data/${country}`);
    },
    getPredictionsByCountry: (country) => {
        return doRequest('GET', `/covid19/rest/predictions/by_country/${country}`);
    },
    getPredictionsByDate: (prediction_name) => {
        return doRequest('GET', `/covid19/rest/predictions/by_prediction/${prediction_name}`);
    },
    getPrediction: (prediction, country) => {
        return doRequest('GET', `/covid19/rest/predictions/by_prediction/${prediction}/${country}`);
    },
    getAbout: () => {
        return fetch('/covid19/rest/about.md')
            .then((response) => {
                if (response.ok) {
                    return response.text();
                } else {
                    throw new Error(response.statusText, response.status);
                }
            });
    }
};