import os


__all__ = (
    # option name constants
    'DLHUB_RT_OPTNAME',
    'DLHUB_AT_OPTNAME',
    'DLHUB_AT_EXPIRES_OPTNAME'
)

# The path to read and write servable definitions.
DLHUB_URL = "https://dlhub.org/"
DLHUB_SERVICE_ADDRESS = "https://api.dlhub.org/api/v1"

CONF_SECTION_NAME = 'dlhub'

CLIENT_ID = 'f47a891c-cfd0-443c-8db8-c72fb82fe3f7'
DLHUB_RT_OPTNAME = 'dlhub_refresh_token'
DLHUB_AT_OPTNAME = 'dlhub_access_token'
DLHUB_AT_EXPIRES_OPTNAME = 'dlhub_access_token_expires'
SEARCH_INDEX = "dlhub"

GLOBUS_ENV = os.environ.get('GLOBUS_SDK_ENVIRONMENT')
if GLOBUS_ENV:
    DLHUB_RT_OPTNAME = '{}_{}'.format(GLOBUS_ENV, DLHUB_RT_OPTNAME)
    DLHUB_AT_OPTNAME = '{}_{}'.format(GLOBUS_ENV, DLHUB_AT_OPTNAME)
    DLHUB_AT_EXPIRES_OPTNAME = '{}_{}'.format(GLOBUS_ENV,
                                              DLHUB_AT_EXPIRES_OPTNAME)
    CLIENT_ID = {
        'sandbox':      'f9e36a20-2e1a-49e5-ba67-34cc82ca8b29',
        'test':         '2aa543de-b6c6-4aa5-9d7b-ef28e3a28cd8',
        'staging':      '0811fdd3-0d3e-4b5e-b634-8d6c91d87f21',
        'preview':      '988ff3e0-3bcf-495a-9f12-3b3a309bdb36',
    }.get(GLOBUS_ENV, CLIENT_ID)
