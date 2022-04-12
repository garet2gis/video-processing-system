FROM node:16-alpine as build

ARG REACT_APP_API_ENDPOINT
ENV REACT_APP_API_ENDPOINT $REACT_APP_API_ENDPOINT

WORKDIR /app
COPY ./package.json ./package.json
COPY ./yarn.lock ./yarn.lock
RUN yarn install --prod --network-timeout 1000000
COPY . .
RUN yarn build

FROM nginx:stable-alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]