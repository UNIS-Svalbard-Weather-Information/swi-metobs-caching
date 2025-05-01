# Svalbard Weather Information (SWI)


[![Tests](https://github.com/LouisPauchet/UNIS_SvalbardWeatherInformation/actions/workflows/pytest.yml/badge.svg)](https://github.com/LouisPauchet/UNIS_SvalbardWeatherInformation/actions/workflows/pytest.yml) [![Pre-release](https://github.com/LouisPauchet/UNIS_SvalbardWeatherInformation/actions/workflows/prerelease.yml/badge.svg)](https://github.com/LouisPauchet/UNIS_SvalbardWeatherInformation/actions/workflows/prerelease.yml) [![Docker Build](https://github.com/LouisPauchet/UNIS_SvalbardWeatherInformation/actions/workflows/build.yml/badge.svg)](https://github.com/LouisPauchet/UNIS_SvalbardWeatherInformation/actions/workflows/build.yml) [![REUSE status](https://api.reuse.software/badge/github.com/LouisPauchet/UNIS_SvalbardWeatherInformation)](https://api.reuse.software/info/github.com/LouisPauchet/UNIS_SvalbardWeatherInformation) [![codecov](https://codecov.io/gh/LouisPauchet/UNIS_SvalbardWeatherInformation/graph/badge.svg?token=YCSP0BAVND)](https://codecov.io/gh/LouisPauchet/UNIS_SvalbardWeatherInformation)    [![Docs](https://app.readthedocs.org/projects/swi-svalbard-weather-information/badge/?version=latest)](https://swi-svalbard-weather-information.readthedocs.io/)


## Overview
The Svalbard Weather Information (SWI) project is a web application designed to assist users in planning trips to Svalbard. It provides essential tools and near real-time weather data from various weather stations in the region. The application includes map layers, avalanche forecasts, sea ice information, regulation layers, and more.

## Features
- **Map Layers**: Visualize different geographical and environmental data layers, including avalanche forecasts, sea ice information, and regulation layers.
- **Real-Time Weather Data**: Access near real-time weather information from multiple weather stations.
- **GPX Import/Export**: Easily import and export GPX files for route planning and sharing.
- **Drawing Tools**: Annotate and draw on maps to customize your trip planning.

## Getting Started

### Prerequisites
- Docker: Ensure Docker is installed on your machine.

### Installation
1. Download the `docker-compose.yml` file.

### Configuration
1. Create a `.env` file in the project root directory.
2. Add your API keys for the different data sources to the `.env` file. For example:
   ```plaintext
   SWI_FROST_API_KEY=your_frost_api_key
   SWI_IWIN_FIXED_API_KEY=your_iwin_api_key
   ```
3. Update the `docker-compose.yml` file to include the environment variables:
   ```yaml
   version: '3.8'
   services:
     swi_cache:
       image: lpauchet/swi-server:latest
       ports:
         - "5000:5000"
       volumes:
         - ./docker_volume/cache:/app/cache
         - ./docker_volume/maps:/app/maps
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

     swi_serve:
       image: lpauchet/swi-server:latest
       ports:
         - "5001:5000"
       volumes:
         - ./docker_volume/cache:/app/cache
         - ./docker_volume/maps:/app/maps
       env_file:
         - .env
       environment:
         - SWI_INSTANCE_SERVE_ONLY=true
         - SWI_DOCKER_INSTANCE=true
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:5000"]
         interval: 30s
         timeout: 10s
         retries: 5
   ```

### Running the Application
1. Start the Docker container:
   ```bash
   docker-compose up
   ```
2. Access the application in your web browser at `http://localhost:5000`. To use the application behind a load balancer, you can multiply the serve instance.

### Production Environment
For production use, it is recommended to set up a load balancer to distribute traffic across multiple instances of the `swi_serve` service. This ensures high availability and reliability. Additionally, consider implementing monitoring and logging to track the application's performance and quickly address any issues that may arise. Note that access logs should be implemented at the load balancer level.

For detailed deployment instructions, refer to the [Deployment Documentation](https://swi-svalbard-weather-information.readthedocs.io/admin/deployment/).

## Automated Workflows
- **Auto Test**: Automated tests are set up to ensure the application runs smoothly.
- **Release**: Automated release workflows are configured for seamless deployment.
- **Build**: Automated build processes are in place to compile the application efficiently.

## Contributing
We welcome contributions from the community. To contribute:
1. Fork the repository.
2. Create a new branch: `git checkout -b feature-new-feature`.
3. Make your changes and commit them: `git commit -am 'Add new feature'`.
4. Push to the branch: `git push origin feature-new-feature`.
5. Submit a pull request.

Feel free to open issues for any bugs, feature requests, or general feedback. Your input is valuable to us!

## License
This project is licensed under the CC0-1.0 License. See the [LICENSE](LICENSE) file for details.