# Multi Cloud Storage

## 1. Setup Instruction

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
    sudo apt-get install libmysqlclient-dev
    pip install -r requirements.txt
    ```

4. Start docker container for database and redis connection. (Optional)

    ```bash
    docker run -p 3306:3306 --name mcos-db -e \
    MYSQL_ROOT_PASSWORD=<mysql_password> -e MYSQL_DATABASE=mcos -d mysql:latest

    <!-- docker run -p 6379:6379 --name mcos-redis -d redis redis-server -->
    ```

5. Go to files ````mcos/settings/local.py```` and ```mcos/settings/mcos_conf.py```,
   and modify your local config

6. Run migrate databse and wsgi server.

    ```bash
    python manage.py migrate  # DB create
    <!-- celery -A mcs worker -P eventlet -c 1000 -l info -->
    python run.py # start wsgi server
    ```

__Note__: For develope & testing environment, clouds may be devstack vms.

- [Minial Swift S3 devstack](https://gist.github.com/ntk148v/f5976e53e545656dd6dd012b908c843f)
- [Minial Swift devstack](https://gist.github.com/ntk148v/2a623e59f10607fd6c0d66f609785a41)

## 2. Setup Object Storage Service In Virtual Machine Guide (Swift S3 Devstack, Swift Devstack)

### Swift Devstack

Following these steps:

- Create a Virtual Machine and install Ubuntu Server 16.04 Xenial on it.
- Create stack user and clone devstack and openstack requirement repo

```bash
sudo useradd -s /bin/bash -d /opt/stack -m stack
echo "stack ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/stack
sudo su - stack
git clone -b mitaka-eol https://git.openstack.org/openstack-dev/devstack
git clone -b stable/mitaka https://git.openstack.org/openstack/requirements
```

- Create or modify two files: ```/opt/stack/devstack/local.conf``` and ```/opt/stack/requirements/upper-constraints.txt```

- File ```/opt/stack/devstack/local.conf```:

```bash
[[local|localrc]]
FORCE=yes
RECLONE=no
#for the first time, set offline = false to clone require packages
#OFFLINE=True
GIT_BASE=http://git.openstack.org
HORIZON_BRANCH=mitaka-eol
KEYSTONE_BRANCH=mitaka-eol
SWIFT_BRANCH=mitaka-eol

#-----------------------------
# Common congigurations
#-----------------------------
disable_all_services
enable_service key mysql
# Enable Swift
enable_service s-proxy s-object s-container s-account
# Enable Horizon
enable_service horizon
enable_plugin horizon-i18n-tools https://github.com/amotoki/horizon-i18n-tools.git

LIBS_FROM_GIT=django_openstack_auth
HORIZONAUTH_BRANCH=mitaka-eol

#-----------------------------
# Devstack configurations
#-----------------------------
# Logging configuration
LOGDIR=$DEST/logs
SCREEN_LOGDIR=$LOGDIR
SCREEN_HARDSTATUS="%{= rw} %H %{= wk} %L=%-w%{= bw}%30L> %n%f %t*%{= wk}%+Lw%-17< %-=%{= gk} %y/%m/%d %c"
LOGFILE=$LOGDIR/devstack.log
LOGDAYS=5
LOG_COLOR=True

# Password configuration
ADMIN_PASSWORD=bkcloud
MYSQL_PASSWORD=bkcloud
RABBIT_PASSWORD=bkcloud
SERVICE_PASSWORD=bkcloud
SERVICE_TOKEN=bkcloud

# Swift
# -----
SWIFT_HASH=bkcloud
SWIFT_REPLICAS=1
SWIFT_DATA_DIR=$DEST/data
```

- File ```/opt/stack/requirements/upper-constraints.txt```:

```bash
...
openstacksdk===0.9.11
```

- put current working directory to devstack folder and run ```stack.sh``` script

```bash
./stack.sh
```

### Swift S3 Devstack

Following these steps:

- Create a Virtual Machine and install Ubuntu Server 16.04 Xenial on it.
- Create stack user and clone devstack and openstack requirement repo

```bash
sudo useradd -s /bin/bash -d /opt/stack -m stack
echo "stack ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/stack
sudo su - stack
git clone -b mitaka-eol https://git.openstack.org/openstack-dev/devstack
git clone -b stable/mitaka https://git.openstack.org/openstack/requirements
```

- Create or modify two files: ```/opt/stack/devstack/local.conf``` and ```/opt/stack/requirements/upper-constraints.txt```

- File ```/opt/stack/devstack/local.conf```:

```bash
[[local|localrc]]
FORCE=yes
RECLONE=no
#for the first time, set offline = false to clone require packages
#OFFLINE=True
GIT_BASE=http://git.openstack.org
HORIZON_BRANCH=mitaka-eol
KEYSTONE_BRANCH=mitaka-eol
SWIFT_BRANCH=mitaka-eol
SWIFT3_BRANCH=v1.11

#-----------------------------
# Common congigurations
#-----------------------------
disable_all_services
enable_service key mysql
# Enable Swift
enable_service s-proxy s-object s-container s-account
enable_service swift3
# Enable Horizon
enable_service horizon
enable_plugin horizon-i18n-tools https://github.com/amotoki/horizon-i18n-tools.git

LIBS_FROM_GIT=django_openstack_auth
HORIZONAUTH_BRANCH=mitaka-eol

#-----------------------------
# Devstack configurations
#-----------------------------
# Logging configuration
LOGDIR=$DEST/logs
SCREEN_LOGDIR=$LOGDIR
SCREEN_HARDSTATUS="%{= rw} %H %{= wk} %L=%-w%{= bw}%30L> %n%f %t*%{= wk}%+Lw%-17< %-=%{= gk} %y/%m/%d %c"
LOGFILE=$LOGDIR/devstack.log
LOGDAYS=5
LOG_COLOR=True

# Password configuration
ADMIN_PASSWORD=bkcloud
MYSQL_PASSWORD=bkcloud
RABBIT_PASSWORD=bkcloud
SERVICE_PASSWORD=bkcloud
SERVICE_TOKEN=bkcloud

# Swift
# -----
SWIFT_HASH=bkcloud
SWIFT_REPLICAS=1
SWIFT_DATA_DIR=$DEST/data
```

- File ```/opt/stack/requirements/upper-constraints.txt```:

```bash
...
openstacksdk===0.9.11
```

- put current working directory to devstack folder and run ```stack.sh``` script

```bash
./stack.sh
```

- create ec2 credential:

```bash
stack@amazons3:~$ . admin.sh
stack@amazons3:~$ openstack ec2 credentials create
stack@amazons3:~$ openstack ec2 credentials list
```
- create ```admin.sh``` file

```bash
export OS_PROJECT_DOMAIN_NAME=default
export OS_USER_DOMAIN_NAME=default
export OS_PROJECT_NAME=admin
export OS_USERNAME=admin
export OS_PASSWORD=bkcloud
export OS_AUTH_URL=http://192.168.122.150:35357/v3
export OS_IDENTITY_API_VERSION=3
export OS_IMAGE_API_VERSION=2
```