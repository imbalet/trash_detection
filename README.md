run to deploy:

```
docker run --device /dev/video2:/dev/video2 --gpus all -p 8080:5000 -v volume:/app/ my-web-server
```