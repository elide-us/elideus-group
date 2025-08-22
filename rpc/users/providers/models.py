from pydantic import BaseModel


class UsersProvidersSetProvider1(BaseModel):
  provider: str


class UsersProvidersLinkProvider1(BaseModel):
  provider: str
  code: str
  code_verifier: str | None = None


class UsersProvidersUnlinkProvider1(BaseModel):
  provider: str


class UsersProvidersGetByProviderIdentifier1(BaseModel):
  provider: str
  provider_identifier: str


class UsersProvidersCreateFromProvider1(BaseModel):
  provider: str
  provider_identifier: str
  provider_email: str
  provider_displayname: str
  provider_profile_image: str | None = None
