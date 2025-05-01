# Application Deployment

## Docker

### General Information

The Docker container operates in two distinct modes:

#### Mode 1: Caching Task

- **Environment Variables:**
  - `SWI_INSTANCE_SERVE_ONLY=false`
  - `SWI_DOCKER_INSTANCE=true`

- **Description:**
  In this mode, the container is responsible for retrieving weather data from various sources and building the map layers. This process is resource-intensive.

- **Resource Requirements:**
  - **RAM:** At least 6GB

#### Mode 2: Web App Serving

- **Environment Variables:**
  - `SWI_INSTANCE_SERVE_ONLY=true`
  - `SWI_DOCKER_INSTANCE=true`

- **Resource Requirements:**
  - Depends on the load

We recommend using Docker Compose for deployment to simplify the process. In the SWI repository, you will find a Docker Compose configuration with two services: `swi_cache` and `swi_serve`. The first service runs in caching mode, as described above, and the second service runs in serving mode.

The idea is to have a container in cache mode that prepares the data stored in two volumes shared across all containers. This data will then be used as a data source by all serving containers. This setup allows you to scale the number of serving containers as needed to handle the load.

The caching container requires API keys to access the different APIs from which the data is retrieved. You can configure these API keys by creating a `.env` file in the root directory (where your `docker-compose.yml` file is located) with the API keys for the different endpoints:

```plaintext
SWI_FROST_API_KEY=your_frost_api_key
SWI_IWIN_FIXED_API_KEY=your_iwin_api_key
```

### Deployment Steps

Here is an example of how to deploy the setup to run two serving containers behind a Caddy reverse proxy as a load balancer.

1. **Create a New Directory**

```sh
mkdir swi
cd swi
```

2. **Fetch the Docker Compose File**

   Download the `docker-compose.yml` file from the repository: [LouisPauchet/UNIS_SvalbardWeatherInformation](https://github.com/LouisPauchet/UNIS_SvalbardWeatherInformation)

```sh
wget https://raw.githubusercontent.com/LouisPauchet/UNIS_SvalbardWeatherInformation/main/docker-compose.yml -O docker-compose.yml
```

3. **Create the API Key `.env` File**

```sh
echo "SWI_FROST_API_KEY=your_frost_api_key" >> .env
echo "SWI_IWIN_FIXED_API_KEY=your_iwin_api_key" >> .env
```

4. **Update the Docker Compose File**

   Modify the `docker-compose.yml` file to include two `swi_serve` services on different ports (e.g., 6501 and 6502) and update the volumes to `./cache` and `./maps`.

5. **Add the Caddy Container to Docker Compose**

   Add the Caddy container configuration to the `docker-compose.yml` file and point it to the `Caddyfile`.

6. **Create a Caddyfile**

```plaintext
http://localhost {
    reverse_proxy swi_serve1:5000 swi_serve2:5000 {
        # Load balancing options
        lb_policy round_robin
    }
}
```

#### Example Docker Compose File

```yaml
services:
  swi_cache:
    image: lpauchet/swi-server:latest
    volumes:
      - ./cache:/app/cache
      - ./maps:/app/maps
    env_file:
      - .env
    environment:
      - SWI_INSTANCE_SERVE_ONLY=false
      - SWI_DOCKER_INSTANCE=true
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - swi_network
    extra_hosts:
      - "host.docker.internal:host-gateway"

  swi_serve1:
    image: lpauchet/swi-server:latest
    volumes:
      - ./cache:/app/cache
      - ./maps:/app/maps
    environment:
      - SWI_INSTANCE_SERVE_ONLY=true
      - SWI_DOCKER_INSTANCE=true
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - swi_network

  swi_serve2:
    image: lpauchet/swi-server:latest
    volumes:
      - ./cache:/app/cache
      - ./maps:/app/maps
    environment:
      - SWI_INSTANCE_SERVE_ONLY=true
      - SWI_DOCKER_INSTANCE=true
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - swi_network

  caddy:
    image: caddy:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
    depends_on:
      - swi_serve1
      - swi_serve2
    networks:
      - swi_network

networks:
  swi_network:
    driver: bridge
```

7. **Run the Containers**

   ```bash
   docker-compose up -d
   ```

## WSGI

## Kubernetes