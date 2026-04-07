ADDON_NAME = 'QRcodeGen'
COMPANY_NAME = ''

# Command identifiers
CMD_ID = 'QRcodeGen_Generate'
CMD_NAME = 'QR Code Creator'
CMD_DESCRIPTION = 'Generate QR codes as 3D bodies for multi-color printing'

# UI Placement
WORKSPACE_ID = 'FusionSolidEnvironment'
TAB_ID = 'SolidTab'
PANEL_ID = 'SolidCreatePanel'

# Default values (in mm, converted to cm for Fusion internally)
DEFAULT_SEGMENT_SIZE_MM = 2.0
DEFAULT_SEGMENT_SPACING_MM = 0.0
DEFAULT_FRAME_SIZE_MM = 2.0
DEFAULT_EXTRUDE_DISTANCE_MM = 1.0

# Creation modes
MODE_SIMPLE = 'Simple'
MODE_WEBSITE = 'Website'
MODE_VCARD = 'vCard'
MODE_WIFI = 'WiFi'
MODE_SEQUENCE = 'Sequence'
CREATION_MODES = [MODE_SIMPLE, MODE_WEBSITE, MODE_VCARD, MODE_WIFI, MODE_SEQUENCE]

# Style options
STYLE_SQUARE = 'Square'
STYLE_CIRCLE = 'Circle'

# Error correction levels
EC_LEVELS = ['L (7%)', 'M (15%)', 'Q (25%)', 'H (30%)']
EC_MAP = {'L (7%)': 'L', 'M (15%)': 'M', 'Q (25%)': 'Q', 'H (30%)': 'H'}
