BAD_PATTERNS = [
    'graph TD',
    '```',
    '| Indicator |',
    '-->',
    '<!--',
]

class VisualQualityError(Exception):
    pass

def validate_text_output(text):
    value = str(text)
    for pattern in BAD_PATTERNS:
        if pattern in value:
            raise VisualQualityError(f'raw visual artifact leaked: {pattern}')
    if len(value.strip()) < 40:
        raise VisualQualityError('visual output is too short to be useful')
    return True
