FROM node:latest

COPY . /app
WORKDIR /app
RUN npm install
RUN npm run build
RUN mv build /
WORKDIR /build
RUN rm -rf /app
