## Development
### Dependencies
You need to have [`NodeJS`](https://nodejs.org/) with [`npm`](https://www.npmjs.com/) or [`yarn`](https://yarnpkg.com/) and backend (see [README](../covid_graphs/README.md)).

1. run `yarn install` or `npm install`. This step is needed only once.
1. execute backend from `../covid_graphs`. See [README](../covid_graphs/README.md) what step are needed.
1. run `yarn start` or `npm start`.

Application should be available at http://localhost:3000/.

## Deployment
1. run `yarn install` or `npm install` if not already did.
1. run `yarn build` or `npm build`.
1. run backend app. See [README](../covid_graphs/README.md).
1. new web should be available under http://localhost:8081/covid19/predictions/graphs/

Final application should be in `build` folder. Application expects that after deployment, following path will be answered by backend.
* `/covid19/predictions/list/`
* `/covid19/predictions/data/*` 
