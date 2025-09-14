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

#### Step 1: Create a New Directory

```sh
mkdir swi
cd swi
```

#### Step 2: Fetch the Docker Compose File

Download the `docker-compose.yml` file from the repository: [LouisPauchet/UNIS_SvalbardWeatherInformation](https://github.com/LouisPauchet/UNIS_SvalbardWeatherInformation)

```sh
wget https://raw.githubusercontent.com/LouisPauchet/UNIS_SvalbardWeatherInformation/master/docker-compose.yml -O docker-compose.yml
```

#### Step 3: Create the API Key `.env` File

```sh
echo "SWI_FROST_API_KEY=your_frost_api_key" >> .env
echo "SWI_IWIN_FIXED_API_KEY=your_iwin_api_key" >> .env
```

#### Step 4: Update the Docker Compose File

Modify the `docker-compose.yml` file to include two `swi_serve` services and update the volumes to `./cache` and `./maps`.

#### Step 5: Add the Caddy Container to Docker Compose

Add the Caddy container configuration to the `docker-compose.yml` file and point it to the `Caddyfile`.

#### Step 6: Create a Caddyfile

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

#### Step 7: Run the Containers

```sh
docker-compose up -d
```

## WSGI

## Kubernetes Deployment

This section provides a step-by-step guide to deploying your application on Kubernetes with autoscaling. The following steps will help you translate your Docker Compose setup into Kubernetes manifests and configure autoscaling. **This section have been generated using a LLM and have not been tested.**

### Step 1: Create a ConfigMap for Environment Variables

First, create a ConfigMap to store your environment variables, including the API keys from your `.env` file.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: swi-env-config
data:
  SWI_FROST_API_KEY: "your_frost_api_key"
  SWI_IWIN_FIXED_API_KEY: "your_iwin_api_key"
```

### Step 2: Create Kubernetes Deployment Manifests

Convert each service in your Docker Compose file into a Kubernetes Deployment. Below are the deployment manifests for the services defined in your Docker Compose file.

#### Deployment for `swi_cache`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: swi-cache
spec:
  replicas: 1
  selector:
    matchLabels:
      app: swi-cache
  template:
    metadata:
      labels:
        app: swi-cache
    spec:
      containers:
      - name: swi-cache
        image: lpauchet/swi-server:latest
        volumeMounts:
        - mountPath: /app/cache
          name: cache-volume
        - mountPath: /app/maps
          name: maps-volume
        envFrom:
        - configMapRef:
            name: swi-env-config
        env:
        - name: SWI_INSTANCE_SERVE_ONLY
          value: "false"
        - name: SWI_DOCKER_INSTANCE
          value: "true"
        livenessProbe:
          httpGet:
            path: /
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 30
      volumes:
      - name: cache-volume
        hostPath:
          path: /path/to/cache
      - name: maps-volume
        hostPath:
          path: /path/to/maps
```

#### Deployment for `swi_serve`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: swi-serve
spec:
  replicas: 2
  selector:
    matchLabels:
      app: swi-serve
  template:
    metadata:
      labels:
        app: swi-serve
    spec:
      containers:
      - name: swi-serve
        image: lpauchet/swi-server:latest
        volumeMounts:
        - mountPath: /app/cache
          name: cache-volume
        - mountPath: /app/maps
          name: maps-volume
        envFrom:
        - configMapRef:
            name: swi-env-config
        env:
        - name: SWI_INSTANCE_SERVE_ONLY
          value: "true"
        - name: SWI_DOCKER_INSTANCE
          value: "true"
        livenessProbe:
          httpGet:
            path: /
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 30
      volumes:
      - name: cache-volume
        hostPath:
          path: /path/to/cache
      - name: maps-volume
        hostPath:
          path: /path/to/maps
```

### Step 3: Set Up Services

Define Kubernetes Services to expose your deployments. This allows your pods to communicate with each other and external clients.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: swi-cache
spec:
  selector:
    app: swi-cache
  ports:
    - protocol: TCP
      port: 5000
      targetPort: 5000
---
apiVersion: v1
kind: Service
metadata:
  name: swi-serve
spec:
  selector:
    app: swi-serve
  ports:
    - protocol: TCP
      port: 5000
      targetPort: 5000
```

### Step 4: Configure Horizontal Pod Autoscaler (HPA)

Set up autoscaling for your deployments based on CPU usage or other metrics. This ensures that your application can handle varying loads efficiently.

```yaml
apiVersion: autoscaling/v2beta2
kind: HorizontalPodAutoscaler
metadata:
  name: swi-serve-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: swi-serve
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
```

### Step 5: Configure Ingress

Use an Ingress resource to manage external access to your services. This is similar to the previous Caddy configuration and allows you to define routing rules.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: swi-ingress
spec:
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: swi-serve
            port:
              number: 5000
```

### Step 6: Apply the Manifests

Use `kubectl apply` to deploy your application and autoscaling configuration to the cluster.

```bash
kubectl apply -f swi-env-configmap.yaml
kubectl apply -f swi-cache-deployment.yaml
kubectl apply -f swi-serve-deployment.yaml
kubectl apply -f swi-services.yaml
kubectl apply -f swi-hpa.yaml
kubectl apply -f swi-ingress.yaml
```

### Notes:

- **ConfigMap**: Update the `swi-env-config` ConfigMap with your actual API keys.
- **Volumes**: Adjust the `hostPath` to match your environment. For production, consider using PersistentVolumeClaims.
- **Ingress**: Replace `your-domain.com` with your actual domain. Ensure you have an Ingress controller installed in your cluster.

This setup will deploy your services on Kubernetes, expose them through Services, and enable autoscaling based on CPU usage. Adjust the configurations as needed for your specific requirements.