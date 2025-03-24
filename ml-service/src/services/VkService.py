import requests


class VkService:
    def __init__(self):
        self.oauth2_url = "https://id.vk.com/authorize"
        self.client_id = "52894113"

    def oauth2_request(self,
                       response_type="code",
                       redirect_uri="http://localhost:8000/",
                       ):
        request_url = f"{self.oauth2_url}?response_type={response_type}&client_id={self.client_id}"
        return request_url
