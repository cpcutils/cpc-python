import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from dataclass_wizard import JSONWizard
from dataclass_wizard.errors import JSONWizardError
from httpx import AsyncClient, HTTPStatusError, RequestError

from .exception import AuthorizationException, ConnectionException


class AbstractAuth(ABC):
  TOKEN_URL = "https://sso-osu.canadapost-postescanada.ca/mga/sps/oauth/oauth20/token"
  CLIENT_ID = "cpc-nativeapp-2020"
  SCOPE = "openid profile"

  @abstractmethod
  async def async_get_access_and_id_token(self, client: AsyncClient) -> tuple[str, str]:
    pass


class DefaultAuth(AbstractAuth):
  def __init__(self, username: str, password: str):
    self._username = username
    self._password = password

    self._oauth_response: Optional[OauthResponse] = None

  async def async_get_access_and_id_token(self, client: AsyncClient) -> tuple[str, str]:
    if self._oauth_response:
      if (
        self._oauth_response.token_expiration - datetime.datetime.now()
        > datetime.timedelta(minutes=1)
      ):
        return self._oauth_response.get_access_and_id_token()
      return await self._async_oauth_flow(
        client, "refresh_token", {"refresh_token": self._oauth_response.refresh_token}
      )
    return await self._async_oauth_flow(
      client, "password", {"username": self._username, "password": self._password}
    )

  async def _async_oauth_flow(
    self, client: AsyncClient, grant_type: str, parameters: dict[str, str]
  ) -> tuple[str, str]:
    data = parameters | {
      "grant_type": grant_type,
      "client_id": AbstractAuth.CLIENT_ID,
      "scope": AbstractAuth.SCOPE,
    }

    try:
      response = await client.post(AbstractAuth.TOKEN_URL, data=data)
      response.raise_for_status()
    except RequestError as e:
      raise ConnectionException(e)
    except HTTPStatusError as e:
      if e.response.status_code in (401, 403):
        raise AuthorizationException(e)
      raise ConnectionException(e)

    try:
      self._oauth_response = OauthResponse.from_json(response.text)
      assert self._oauth_response is not None
    except JSONWizardError as e:
      raise ConnectionException(e)

    return self._oauth_response.get_access_and_id_token()


@dataclass
class OauthResponse(JSONWizard):
  access_token: str
  id_token: str
  refresh_token: str
  expires_in: int

  token_expiration = datetime.datetime.now()

  def __post_init__(self):
    self.token_expiration += datetime.timedelta(seconds=self.expires_in)

  def get_access_and_id_token(self) -> tuple[str, str]:
    return self.access_token, self.id_token
