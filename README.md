# FOCOS (Fuzzy Operational Cognition of Safety Culture)
---
## Running the App Locally - Mac/Linux/Windows
1. Pull this repo to your local machine
2. Install Docker if you do not have it already installed
    - Run ``` docker --version``` to verify 
3. Open the folder you cloned the repo into with Powershell
    - cd path/to/folder
4. Update the Dockerfile with the your Github email and preffered name in the "Set git user name and password" section
5. Change the MYSQL_ROOT_PASSWORD and DB_PASSWORD to use these credentials for login to SQL and the app 
6. Run ./RunDocker.ps1
7. Open the flask-app-1 container and go to /app folder
    - For Windows use VSCode 
    - For Linux or Mac use: docker exec -it focos-flask-app-1 (or the container name provided by Docker for the flask app) /bin/bash