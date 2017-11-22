import keystoneclient
import keystoneauth1
from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3.client import Client
from keystoneauth1.exceptions.base import ClientException
from mcos.settings import \
    KEYSTONE_AUTH_URL, KEYSTONE_USER_DOMAIN_ID, KEYSTONE_PROJECT_DOMAIN_NAME, \
    KEYSTONE_PROJECT, KEYSTONE_ADMIN_PASSWORD, KEYSTONE_ADMIN_USERNAME


class KeyStoneClient(Client):
    TOKEN_NOT_FOUND = 1
    TOKEN_EXPIRED = 2
    TOKEN_SUCCESS = 3
    TOKEN_FAILED = 4

    def __init__(self, user_name=None, password=None, token=None):
        if user_name is not None and password is not None:
            auth = v3.Password(
                auth_url=KEYSTONE_AUTH_URL,
                username=user_name,
                password=password,
                project_name=KEYSTONE_PROJECT,
                user_domain_id=KEYSTONE_USER_DOMAIN_ID,
                project_domain_name=KEYSTONE_PROJECT_DOMAIN_NAME)
            sess = session.Session(auth=auth)
        elif token is not None:
            auth = v3.Token(
                auth_url=KEYSTONE_AUTH_URL,
                token=token,
                project_name=KEYSTONE_PROJECT,
                project_domain_name=KEYSTONE_PROJECT_DOMAIN_NAME
            )
            sess = session.Session(auth=auth)
        else:
            raise ClientException("client information must contains username"
                                  "and password or token")
        super(KeyStoneClient, self).__init__(session=sess)
        self.user_id = self.session.get_user_id()
        self.project_id = self.session.get_project_id()

    @staticmethod
    def create_admin_client():
        auth = v3.Password(
            auth_url=KEYSTONE_AUTH_URL,
            username=KEYSTONE_ADMIN_USERNAME,
            password=KEYSTONE_ADMIN_PASSWORD,
            project_name=KEYSTONE_PROJECT,
            user_domain_id=KEYSTONE_USER_DOMAIN_ID,
            project_domain_name=KEYSTONE_PROJECT_DOMAIN_NAME)
        sess = session.Session(auth=auth)
        return Client(session=sess)

    def has_role(self, role_name):
        try:
            admin_client = KeyStoneClient.create_admin_client()
            check_role = admin_client.roles.find(name=role_name)
            admin_client.roles.check(check_role, user=self.user_id,
                                     project=self.project_id)
            return True
        except ClientException as e:
            return False

    @staticmethod
    def create_user(user_name, password):
        try:
            admin_client = KeyStoneClient.create_admin_client()
            keystone_project = admin_client.projects.find(
                name=KEYSTONE_PROJECT)
            created_user = admin_client.users.create(
                name=user_name,
                password=password,
                default_project=keystone_project)
            user_role = admin_client.roles.find(name='user')

            admin_client.roles.grant(role=user_role, user=created_user,
                                     project=keystone_project)
        except Exception as e:
            print(e)
            raise ClientException(
                "This user name already exist!"
                " Choose another user name"
            )

    @staticmethod
    def verify_token_with_role(token, required_role=None):
        if token is None:
            return KeyStoneClient.TOKEN_NOT_FOUND
        else:
            try:
                admin_client = KeyStoneClient.create_admin_client()
                access_info = admin_client.tokens.validate(token)
                has_role = False
                for role in access_info.role_names:
                    if role == required_role:
                        has_role = True
                if has_role:
                    return KeyStoneClient.TOKEN_SUCCESS
                else:
                    return KeyStoneClient.TOKEN_FAILED
            except Exception as e:
                print(e)
                return KeyStoneClient.TOKEN_EXPIRED

    @staticmethod
    def get_request_user_data(request):
        token = request.session.get('auth_token')
        if token is None:
            token = request.META.get('HTTP_X_AUTH_TOKEN', None)
        admin_client = KeyStoneClient.create_admin_client()
        access_info = admin_client.tokens.validate(token)
        return access_info
    @staticmethod
    def logout(request):
        token = request.session.get('auth_token')
        if token is None:
            token = request.META.get('HTTP_X_AUTH_TOKEN', None)
        return KeyStoneClient.create_admin_client().tokens.revoke_token(token)
