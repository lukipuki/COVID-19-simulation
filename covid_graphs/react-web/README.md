## Development
### Local development
You need to have [`NodeJS`](https://nodejs.org/) with [`npm`](https://www.npmjs.com/) or [`yarn`](https://yarnpkg.com/) and backend (see [README](../covid_graphs/README.md)).

1. run `npm install` or `yarn install`. This step is needed only once.
1. execute backend from `../covid_graphs`. See [README](../README.md) what step are needed.
1. run `yarn start` or `npm start`.

Application should be available at http://localhost:3000/.

## Deployment
1. run `npm install` or `yarn install` if not already did.
1. run `npm build` or `yarn build`.
1. run backend app. See [README](../README.md).
1. new web should be available under http://localhost:8081/covid19/predictions/graphs/

Final application should be in `build` folder. Application expects that after deployment, following paths will be answered by backend.
* `/covid19/data/*`
* `/covid19/predictions/list/`
* `/covid19/predictions/data/*`
