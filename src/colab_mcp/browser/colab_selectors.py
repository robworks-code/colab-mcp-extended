"""Centralized Colab DOM selectors. If Colab's UI changes, fix them here only."""

# Runtime menu + dialog
RUNTIME_MENU_BUTTON = 'text="Runtime"'
CHANGE_RUNTIME_TYPE_ITEM = 'text="Change runtime type"'
ACCELERATOR_DROPDOWN = 'mwc-select[aria-label="Hardware accelerator"], #accelerator'
SAVE_BUTTON = 'paper-button#ok, text="Save"'

# Connect / runtime status
CONNECT_BUTTON = 'colab-connect-button, #connect'
CONNECTED_BADGE = 'text="Connected"'

# Factory reset
DISCONNECT_DELETE_ITEM = 'text="Disconnect and delete runtime"'
CONFIRM_YES_BUTTON = 'paper-button#ok, text="Yes"'

# Drive mount consent (popup window)
DRIVE_CONSENT_ALLOW = 'text="Connect to Google Drive"'

# Save indicator
SAVING_DONE_INDICATOR = 'text="All changes saved"'
