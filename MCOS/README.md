# Multi Cloud Storage

Follow these steps:

1. Clone CAL\_Appliances repository:

    ```bash
    git clone https://github.com/HPCC-Cloud-Computing/CAL_Appliances
    ```

2. Checkout branch mcos

    ```bash
    git checkout mcos
    cd MCOS
    ```

3. Install requirements:

    ```bash
    pip install -r requirements.txt
    ```

4. Start docker container for database and redis connection. (Optional)

    ```bash
    docker run -p 3306:3306 --name mcos-db -e \
    MYSQL_ROOT_PASSWORD=<mysql_password> -e MYSQL_DATABASE=mcos -d mysql:latest

    <!-- docker run -p 6379:6379 --name mcos-redis -d redis redis-server -->
    ```

5. Go to mcos/settings/local.py, and fill your container's ip and password.

6. Run migrate databse and wsgi server.

    ```bash
    python manage.py migrate  # DB create
    <!-- celery -A mcs worker -P eventlet -c 1000 -l info -->
    python run.py # start wsgi server
    ```

__Note__: For develope & testing environment, clouds may be devstack vms.

- [Minial Swift S3 devstack](https://gist.github.com/ntk148v/f5976e53e545656dd6dd012b908c843f)
- [Minial Swift devstack](https://gist.github.com/ntk148v/2a623e59f10607fd6c0d66f609785a41)

