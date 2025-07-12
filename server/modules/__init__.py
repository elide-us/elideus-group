from abc import ABC
from fastapi import FastAPI

class BaseModule(ABC):
  def __init__(self, app: FastAPI):
    self.app = app
