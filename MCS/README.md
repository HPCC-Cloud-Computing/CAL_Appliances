# Multi Cloud Storage

Follow these steps:

1. Clone CAL\_Appliances repository:

    ```
    git clone https://github.com/HPCC-Cloud-Computing/CAL_Appliances
    ```

2. Checkout branch mcs/core.

    ```
    git checkout mcs/core
    cd MCS/
    ```

3. Install requirements:

    ```
    pip install -r requirements.txt
    ```

4. Start docker container for database and redis connection.

    ```
    docker run -p 3306:3306 --name mcs-db -e \
    MYSQL_ROOT_PASSWORD=<mysql_password> -e MYSQL_DATABASE=mcs -d mysql:latest

    docker run --name mcs-redis -d redis redis-server --requirepass "<redis_password>"
    ```

5. Go to mcs/settings/local.py, and fill your container's ip and password.

6. Run migrate databse and wsgi server.

    ```
    python manage.py migrate
    python mcs/wsgi.py
    ```

7. Open browser, go to http://127.0.0.1:8080/auth/register and complete
   register step. Then login into MCS. MCS will redirect to /lookup/init\_ring/,
   please choose your config file (Take a look at my sample-config file).


__Note__: For develope & testing environment, clouds may be devstack vms.

- [Minial Swift S3 devstack](https://gist.github.com/ntk148v/f5976e53e545656dd6dd012b908c843f)
- [Minial Swift devstack](https://gist.github.com/ntk148v/2a623e59f10607fd6c0d66f609785a41)

