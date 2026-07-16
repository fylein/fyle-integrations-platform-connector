import logging
from datetime import timedelta

from django.utils import timezone

from apps.workspaces.models import FyleCredential

logger = logging.getLogger(__name__)
logger.level = logging.INFO

ACCESS_TOKEN_EXPIRY_MINUTES = 30


def is_access_token_valid(fyle_credentials: FyleCredential) -> bool:
    """
    Check if the Fyle access token is valid for the given FyleCredential instance.
    :param fyle_credentials: FyleCredential instance containing access token and expiry information.
    :return: True if the access token is valid, False otherwise.
    """
    if not hasattr(fyle_credentials, 'access_token'):
        logger.info('Fyle access token not found in fyle_credentials model for workspace_id %s', fyle_credentials.workspace_id)
        return False

    if not fyle_credentials.access_token:
        logger.info('Fyle access token not found for workspace_id %s', fyle_credentials.workspace_id)
        return False

    if not fyle_credentials.access_token_expires_at:
        logger.info('Fyle access token expiry not found for workspace_id %s; refreshing token', fyle_credentials.workspace_id)
        return False

    if fyle_credentials.access_token_expires_at <= timezone.now():
        logger.info(
            'Fyle access token expired for workspace_id %s at %s; refreshing token', fyle_credentials.workspace_id, fyle_credentials.access_token_expires_at)
        return False

    logger.info('Fyle access token found for workspace_id %s and valid until %s', fyle_credentials.workspace_id, fyle_credentials.access_token_expires_at)
    return True


def get_valid_access_token(fyle_credentials: FyleCredential) -> str | None:
    """
    Get a valid Fyle access token for the given FyleCredential instance.
    If the access token is valid, it will be returned. Otherwise, None will be returned
    to indicate that a new access token needs to be generated using the refresh token.
    :param fyle_credentials: FyleCredential instance containing access token and expiry information.
    :return: Valid access token if available, None otherwise.
    """
    if is_access_token_valid(fyle_credentials):
        return fyle_credentials.access_token

    logger.info('Fyle access token will be generated using refresh token for workspace_id %s', fyle_credentials.workspace_id)
    return None


def save_access_token(fyle_credentials: FyleCredential, access_token: str, generated_at=None) -> None:
    """
    Save the Fyle access token and its expiry time for the given FyleCredential instance.
    :param fyle_credentials: FyleCredential instance to save the access token for.
    :param access_token: The Fyle access token to be saved.
    :param generated_at: The time when the access token was generated. If not provided,
                         the current time will be used.
    :return: None
    """
    if not access_token:
        logger.info('Fyle access token not saved for workspace_id %s because token is empty', fyle_credentials.workspace_id)
        return
    
    if not hasattr(fyle_credentials, 'access_token'):
        logger.info('Fyle access token not saved for workspace_id %s because fyle_credentials model does not have access_token field', fyle_credentials.workspace_id)
        return

    generated_at = generated_at or timezone.now()
    fyle_credentials.access_token = access_token
    fyle_credentials.access_token_expires_at = generated_at + timedelta(
        minutes=ACCESS_TOKEN_EXPIRY_MINUTES
    )
    fyle_credentials.save(update_fields=['access_token', 'access_token_expires_at', 'updated_at'])
    logger.info('Saved Fyle access token for workspace_id %s; expires_at %s', fyle_credentials.workspace_id, fyle_credentials.access_token_expires_at)
