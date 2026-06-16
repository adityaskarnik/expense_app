if [ -n "$(sudo docker ps -aq)" ]; then
  sudo docker stop $(sudo docker ps -aq)
  sudo docker rm $(sudo docker ps -aq)
fi

sudo docker rmi -f $(sudo docker images -aq)
sudo docker system prune -f
sudo docker compose up --build