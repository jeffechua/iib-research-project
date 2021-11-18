docker-compose -f ./docker/docker-compose.yml build --force-rm
docker-compose -f ./docker/docker-compose.yml up -d --force-recreate
python -m http.server 8000
