import os
import re
import requests

ENDPOINT = 'https://ttp.cbp.dhs.gov'

def get_slots_for_location(location_id):
    params = {'orderBy': 'soonest', 'minimum': 1, 'limit': 3, 'locationId': location_id}
    rsp = requests.get(f'{ENDPOINT}/schedulerapi/slots', params)
    return rsp.json()

def get_locations(temporary=False, invite_only=False, operational=True, service_name='Global Entry'):
    params = {'temporary': temporary, 'inviteOnly': invite_only, 'operational': operational, 'serviceName': service_name}
    rsp = requests.get(f'{ENDPOINT}/schedulerapi/locations/', params)
    return rsp.json()

def check_appointments():
    location_ids = os.environ['LOCATION_IDS']
    if not location_ids or not re.match(r'^(\d+,)*(\d+)$', location_ids):
        raise ValueError(f'Bad location IDs: {location_ids}')

    location_ids = [int(x) for x in location_ids.split(',')]
    target_dates_raw = os.environ.get('TARGET_DATES', '')
    target_dates = [d.strip() for d in target_dates_raw.split(',') if d.strip()]

    locations = get_locations()
    locations_by_id = {location['id']: location for location in locations}

    for location_id in location_ids:
        if location_id not in locations_by_id:
            raise ValueError(f'Unknown location ID {location_id}')

   slots_by_date = {}
    for location_id in location_ids:
        slots = get_slots_for_location(location_id)
        location_name = locations_by_id[location_id]['name']
        for slot in slots:
            slot_date = slot['startTimestamp'][:10]
            if target_dates and slot_date not in target_dates:
                continue
            line = f"{location_name}: {slot['startTimestamp']} - {slot['endTimestamp']} ({slot['duration']} minutes)"
            slots_by_date.setdefault(slot_date, []).append(line)

    matching_slots = []
    for date, lines in slots_by_date.items():
        if len(lines) >= 2:
            matching_slots.extend(lines)

    for line in matching_slots:
        print(line)

    return matching_slots

def main():
    try:
        matching_slots = check_appointments()
        with open('slots.txt', 'w') as f:
            f.write('\n'.join(matching_slots))
    except Exception as ex:
        print(ex)
        with open('slots.txt', 'w') as f:
            f.write('')

if __name__ == '__main__':
    main()
