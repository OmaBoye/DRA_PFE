# analysis/utils.py
def format_equipment_data(raw_data):
    """Convert equipment-specific JSON to standard format"""
    # Handle case-insensitive keys
    wbc_value = raw_data.get('wbc') or raw_data.get('WBC', 0)
    hgb_value = raw_data.get('hgb') or raw_data.get('HGB', 0)

    return {
        'hematology': {
            'WBC': {
                'value': float(wbc_value),
                'unit': '10^3/μL',
                'range': '4.0-11.0'
            },
            'HGB': {
                'value': float(hgb_value),
                'unit': 'g/dL',
                'range': '12.0-16.0'
            }
        }
    }