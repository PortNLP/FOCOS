# Set git user name and password
git config --global user.email "aketh.tm@gmail.com"
git config --global user.name "Aketh"

# Creating Docker image
docker-compose build --no-cache
docker-compose up