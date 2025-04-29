# Use the official Node.js image as the base image
FROM node:16

# Set working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json to install dependencies
COPY ./package.json ./package-lock.json /app/

# Install the frontend dependencies
RUN npm install

# Copy the rest of the frontend app code into the container
COPY ./src /app/src
COPY ./public /app/public

# Expose the port the React app will run on
EXPOSE 3000

# Start the React app
CMD ["npm", "start"]
