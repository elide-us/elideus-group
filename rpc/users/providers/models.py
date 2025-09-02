from pydantic import BaseModel


class UsersProvidersSetProvider1(BaseModel):
  provider: str


class UsersProvidersLinkProvider1(BaseModel):
  provider: str
  code: str | None = None
  id_token: str | None = None
  access_token: str | None = None


class UsersProvidersUnlinkProvider1(BaseModel):
  provider: str
  new_default: str | None = None


class UsersProvidersGetByProviderIdentifier1(BaseModel):
  provider: str
  provider_identifier: str


class UsersProvidersCreateFromProvider1(BaseModel):
  provider: str
  provider_identifier: str
  provider_email: str
  provider_displayname: str
  provider_profile_image: str | None = None
