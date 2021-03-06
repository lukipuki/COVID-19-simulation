const { createProxyMiddleware } = require('http-proxy-middleware');

const static_json = function(path, request) {
    if (path === '/covid19/rest/about.md') {
        return 'rest/about.md';
    }

    return path.split('/covid19/')[1] + '.json';
};

module.exports = function(app) {
    app.use(
        '/covid19/rest/',
        createProxyMiddleware({
            target: 'http://localhost:3000',
            pathRewrite: static_json
        })
    );
};