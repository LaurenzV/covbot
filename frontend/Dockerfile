FROM node:16.14 as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY ./ .
RUN npm run build

FROM nginx as production-stage
RUN mkdir /app
COPY --from=build-stage /app/dist /app
COPY nginx.conf /etc/nginx/nginx.conf
COPY certs/cert.pem /etc/nginx/certs/
COPY certs/privkey.pem /etc/nginx/certs/
EXPOSE 80 443