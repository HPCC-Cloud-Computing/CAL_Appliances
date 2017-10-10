# Keystone Client Document

## Basic connect

```python
import keystoneclient
import keystoneauth1
from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client

auth = v3.Password(auth_url="http://172.20.4.1:5000/v3", username="admin",
                   password="bkcloud", project_name="admin",
                   user_domain_id="default", project_domain_id="default")
sess = session.Session(auth=auth)
keystone = client.Client(session=sess)
users = keystone.users.list()
print users

```