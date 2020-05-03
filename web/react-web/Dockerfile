FROM node:latest

COPY . /app-source
WORKDIR /app-source
RUN npm install
RUN npm run build
RUN mv build /app
WORKDIR /app
RUN rm -rf /app-source
