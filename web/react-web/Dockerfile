FROM node:latest

ADD package.json package-lock.json /app-source/
WORKDIR /app-source/
RUN npm install
ADD . /app-source/
RUN npm run build
RUN mv build /app
WORKDIR /app
RUN rm -rf /app-source
