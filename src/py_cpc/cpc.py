from typing import Optional

import jwt
from httpx import AsyncClient

from .auth import AbstractAuth
from .exception import AuthorizationException, ConnectionException
from .generated.client import AuthenticatedClient
from .generated.client.api.default import get_notifications_cpcid
from .generated.client.errors import UnexpectedStatus
from .generated.client.models.my_mail_error import MyMailError


class PyCpc:
  API_URL = "https://1i5z3519d0.execute-api.ca-central-1.amazonaws.com/mailmanager/v1"

  def __init__(self, auth: AbstractAuth):
    self._auth = auth
    self._client: Optional[AsyncClient] = None

  def set_auth(self, auth: AbstractAuth):
    self._auth = auth

  # TODO setting a client will clobber base_url, headers, etc., hence why it's not currently used to make API calls
  # other than to get tokens
  def set_client(self, client: Optional[AsyncClient]):
    self._client = client

  async def async_fetch_incoming_mail(self):
    if not self._client:
      self._client = AsyncClient()

    access_token, id_token = await self._auth.async_get_access_and_id_token(
      self._client
    )
    try:
      cpc_id = jwt.decode(
        id_token, options={"verify_signature": False, "require": ["sub"]}
      )["sub"]
    except jwt.MissingRequiredClaimError as e:
      raise ConnectionException(e)

    authenticated_client = AuthenticatedClient(
      PyCpc.API_URL, f"{access_token}.{id_token}", raise_on_unexpected_status=True
    )

    try:
      response = await get_notifications_cpcid.asyncio(
        cpc_id, client=authenticated_client, day_span=0
      )
    except UnexpectedStatus as e:
      raise ConnectionException(e)

    if isinstance(response, MyMailError):
      raise AuthorizationException(response.message)
    assert response is not None
