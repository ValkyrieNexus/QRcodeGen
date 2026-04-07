"""QR code matrix generation and data encoding logic."""

import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H

EC_MAP = {
    'L': ERROR_CORRECT_L,
    'M': ERROR_CORRECT_M,
    'Q': ERROR_CORRECT_Q,
    'H': ERROR_CORRECT_H,
}


def generate_matrix(data, ec_level='H', border=4):
    """Generate a QR code boolean matrix.

    Args:
        data: String data to encode.
        ec_level: Error correction level ('L', 'M', 'Q', 'H').
        border: Number of border modules (QR spec minimum is 4).

    Returns:
        list[list[bool]]: 2D matrix where True = dark module.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=EC_MAP.get(ec_level, ERROR_CORRECT_H),
        box_size=1,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr.get_matrix()


def clear_center_zone(matrix, zone_modules):
    """Clear a square zone in the center of the matrix for icon placement.

    Args:
        matrix: The QR boolean matrix (modified in place).
        zone_modules: Number of modules to clear on each side of center.

    Returns:
        tuple: (start_row, start_col, end_row, end_col) of cleared zone.
    """
    n = len(matrix)
    if zone_modules <= 0 or zone_modules >= n:
        return None

    # Ensure odd for clean centering
    if zone_modules % 2 == 0:
        zone_modules += 1

    start = (n - zone_modules) // 2
    end = start + zone_modules

    for r in range(start, end):
        for c in range(start, end):
            matrix[r][c] = False

    return (start, start, end, end)


def compute_icon_zone_modules(matrix, icon_size_pct):
    """Compute how many modules the icon zone should span.

    Args:
        matrix: The QR boolean matrix.
        icon_size_pct: Icon size as percentage of QR code (10-30).

    Returns:
        int: Number of modules for the icon zone side length.
    """
    n = len(matrix)
    zone = max(3, int(n * icon_size_pct / 100))
    if zone % 2 == 0:
        zone += 1
    return zone


def compute_rectangles(matrix, dark=True):
    """Compute individual rectangles for each module.

    Args:
        matrix: QR boolean matrix.
        dark: If True, return rectangles for dark modules. If False, for light.

    Returns:
        list[tuple]: List of (row, col) for each module to draw.
    """
    rects = []
    for r, row in enumerate(matrix):
        for c, val in enumerate(row):
            if val == dark:
                rects.append((r, c))
    return rects


def _vcard_escape(value):
    """Escape special characters in vCard field values per RFC 6350."""
    if not value:
        return value
    # Backslash must be escaped first to avoid double-escaping
    value = value.replace('\\', '\\\\')
    value = value.replace(';', '\\;')
    value = value.replace(',', '\\,')
    value = value.replace('\n', '\\n')
    value = value.replace('\r', '')
    return value


def encode_vcard(fields):
    """Encode contact information as a vCard QR string.

    Args:
        fields: dict with keys: first_name, last_name, phone, mobile,
                email, company, job, street, city, zip, state, country, website

    Returns:
        str: vCard formatted string.
    """
    lines = ['BEGIN:VCARD', 'VERSION:3.0']

    fn = _vcard_escape(fields.get('first_name', ''))
    ln = _vcard_escape(fields.get('last_name', ''))
    if fn or ln:
        lines.append(f'N:{ln};{fn};;;')
        full_name = f'{fields.get("first_name", "")} {fields.get("last_name", "")}'.strip()
        lines.append(f'FN:{_vcard_escape(full_name)}')

    if fields.get('company'):
        lines.append(f'ORG:{_vcard_escape(fields["company"])}')
    if fields.get('job'):
        lines.append(f'TITLE:{_vcard_escape(fields["job"])}')
    if fields.get('phone'):
        lines.append(f'TEL;TYPE=WORK,VOICE:{fields["phone"]}')
    if fields.get('mobile'):
        lines.append(f'TEL;TYPE=CELL:{fields["mobile"]}')
    if fields.get('email'):
        lines.append(f'EMAIL:{fields["email"]}')

    # Address -- semicolons are structural delimiters in ADR, so escape
    # only within each individual field component
    street = _vcard_escape(fields.get('street', ''))
    city = _vcard_escape(fields.get('city', ''))
    state = _vcard_escape(fields.get('state', ''))
    zip_code = _vcard_escape(fields.get('zip', ''))
    country = _vcard_escape(fields.get('country', ''))
    if any([street, city, state, zip_code, country]):
        lines.append(f'ADR;TYPE=WORK:;;{street};{city};{state};{zip_code};{country}')

    if fields.get('website'):
        lines.append(f'URL:{fields["website"]}')

    lines.append('END:VCARD')
    return '\n'.join(lines)


def encode_wifi(ssid, password='', encryption='WPA'):
    """Encode WiFi credentials as a QR string.

    Args:
        ssid: Network name.
        password: Network password.
        encryption: 'WPA', 'WEP', or 'nopass'.

    Returns:
        str: WiFi QR formatted string.
    """
    # Escape special characters in SSID and password
    def escape(s):
        return s.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('"', '\\"').replace(':','\\:')

    enc = encryption if encryption in ('WPA', 'WEP', 'nopass') else 'WPA'
    parts = [f'WIFI:T:{enc}', f'S:{escape(ssid)}']
    if password and enc != 'nopass':
        parts.append(f'P:{escape(password)}')
    parts.append(';')
    return ';'.join(parts)


def generate_sequence_data(template, start, end, leading_zeros=0):
    """Generate a list of strings for sequence/batch QR codes.

    Args:
        template: String with /#/ placeholder for the number.
        start: Starting number.
        end: Ending number (inclusive).
        leading_zeros: Total digits with leading zeros (e.g., 3 → "001").

    Returns:
        list[str]: List of formatted strings.
    """
    results = []
    width = max(leading_zeros, len(str(end)))
    for i in range(start, end + 1):
        num_str = str(i).zfill(width)
        results.append(template.replace('/#/', num_str))
    return results


def estimate_qr_version(data, ec_level='H'):
    """Estimate the QR version that will be used for the given data.

    Returns:
        tuple: (version, module_count) where module_count = version*4 + 17
    """
    try:
        qr = qrcode.QRCode(
            version=None,
            error_correction=EC_MAP.get(ec_level, ERROR_CORRECT_H),
            box_size=1,
            border=0,
        )
        qr.add_data(data)
        qr.make(fit=True)
        version = qr.version
        module_count = version * 4 + 17
        return (version, module_count)
    except Exception:
        return (None, None)
