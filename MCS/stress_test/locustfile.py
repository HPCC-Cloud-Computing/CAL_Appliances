from locust import HttpLocust, TaskSet, task


class UserBehavior(TaskSet):

    def on_start(self):
        """on_start is called when a Locust start before any task is scheduled"""
        self.login()

    def login(self):
        # GET login page to get csrftoken from it
        response = self.client.get('/auth/login/')
        csrftoken = response.cookies['csrftoken']
        self.client.headers['Referer'] = self.client.base_url
        # POST to login page with csrftoken
        self.client.post('/auth/login/',
                         {'username': 'kiennt', 'password': 'ntk260994',
                          'csrfmiddlewaretoken': csrftoken},
                         headers={'X-CSRFToken': csrftoken})

    @task(2)
    def home(self):
        self.client.get('/home/')

    @task(1)
    def upload(self):
        self.client.get('/files/upload/')


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 3000
    max_wait = 5000

