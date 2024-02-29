# openvpn-user-monitoring

## Linting
```bash
python -m pylint src/*.py
```

# Docker

```bash
docker build -t openvpn-user-monitoring .
```

```bash
docker run -e ELASTICSEARCH_HOST=<host> -e ELASTICSEARCH_USERNAME=<username> -e ELASTICSEARCH_PASSWORD=<password> -v ./src/openvpn-status.log:/var/log/openvpn/openvpn-status.log openvpn-user-monitoring:latest
```