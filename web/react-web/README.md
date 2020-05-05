## Development
### Local development
You need to have [`NodeJS`](https://nodejs.org/) with [`npm`](https://www.npmjs.com/) or [`yarn`](https://yarnpkg.com/) and backend (see [README](../covid_graphs/README.md)).

1. run `npm install` or `yarn install`. This step is needed only once.
1. execute backend from. See [README](../README.md) what step are needed.
1. run `yarn start` or `npm start`.

Application should be available at http://localhost:3000/.

### Building
1. run `npm install` or `yarn install` if not already did.
1. run `npm build` or `yarn build`.

Final application should be in `build` folder

## Running the whole server

In the root directory of the repository, run `docker-compose`.
```sh
docker-compose up --build # Optionally add -d for daemon
```
You can then access the server locally at [localhost:8081](http://127.0.0.1:8081/covid19/graphs/).

Application expects that after deployment, following paths will be answered by backend.
* `/covid19/rest/data/*`
* `/covid19/rest/predictions/list/`
* `/covid19/rest/predictions/data/*`

