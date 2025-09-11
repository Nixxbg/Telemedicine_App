# Use Node.js 20 as a base image
FROM node:20-slim

# Set the working directory in the container
WORKDIR /app

# Install bun
RUN npm install -g bun

# Copy package.json and bun.lock to leverage Docker cache
COPY package.json bun.lock* ./

# Install dependencies using bun
RUN bun install --frozen-lockfile

# Copy the rest of the application code
COPY . .

# Expose port 3000 for the Next.js app
EXPOSE 3000

# The command to run the development server will be specified in docker-compose.yml
CMD ["bun", "run", "dev"]
