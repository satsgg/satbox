FROM node:18.16.1

WORKDIR /usr/src/app

COPY package.json yarn.lock tsconfig.json .
COPY src src

RUN yarn install

EXPOSE 5000
CMD [ "yarn", "start" ]
