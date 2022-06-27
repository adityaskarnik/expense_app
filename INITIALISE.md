Start with:
Stop all the containers if not required
```
sudo docker stop $(sudo docker ps -aq)
```
Remove all containers
```
sudo docker rm $(sudo docker ps -aq)
```

Remove all image to save space if they are not required
```
sudo docker rmi -f $(sudo docker images -aq)
```

If you have bind error for 5432 port already running and cannot start a container, user command to find the Process ID and then kill the process
```
sudo netstat -nlp | grep :5432
```
```
sudo kill -9 $PID
```

Intialise Docker Swarm
```
sudo docker swarm init
```

Swarm initialized: current node (06halyliauhmsjb3p5gl2shgy) is now a manager.

To add a worker to this swarm, run the following command:
```
    sudo docker swarm join --token SWMTKN-1-2yc44np8s0xnm4klxg04usqbp3h9v7eg6d3nre2klh4c3svvob-6hig9zfinpk3b88umq64m2j4m 192.168.1.21:2377
```
To add a manager to this swarm, run 'docker swarm join-token manager' and follow the instructions.


```
sudo docker-compose up --build
```

