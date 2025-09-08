import logging
from server.helpers.logging import update_logging_level

def test_update_logging_level_sets_warning_for_azure_logger():
  update_logging_level(3)
  azure_logger = logging.getLogger('azure.core.pipeline.policies.http_logging_policy')
  assert azure_logger.level == logging.WARNING

def test_update_logging_level_debug_enables_info_for_azure_logger():
  update_logging_level(4)
  azure_logger = logging.getLogger('azure.core.pipeline.policies.http_logging_policy')
  assert azure_logger.level == logging.INFO
