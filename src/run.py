import os
import re
import requests

ENDPOINT = 'https://ttp.cbp.dhs.gov'

def get_slots_for_location(location_id):
    params = {
        'orderBy': 'soonest',
        'minimum': 1,
        'limit': 3,
        'locationId': location_id,
    }
    rsp = requests.get(f'{ENDPOINT}/schedulerapi/slots', params)
    return rsp.json()

def get_locations(
        temporary=False,
        invite_only=False,
        operational=True,
        service_name='Global Entry'):
    params = {
        'temporary': temporary,
        'inviteOnly': invite_only,
        'operational': operational,
        'serviceName': service_name,
    }
    rsp = requests.get(f'{ENDPOINT}/schedulerapi/locations/', params)
    return rsp.json()

def any_appointment_slots_open():
    location_ids = os.environ['LOCATION_IDS']
    if not location_ids or not re.match(r'^(\d+,)*(\d+)$', location_ids):
        raise ValueError(f'Bad location IDs: {location_ids}')

    location_ids = [int(x) for x in location_ids.split(',')]

    # Optional: only notify for slots on specific dates (e.g. "2025-09-15,2025-09-16")
    target_dates_raw = os.environ.get('TARGET_DATES', '')
    target_dates = [d.strip() for d in target_dates_raw.split(',') if d.strip()]

    locations = get_locations()
    locations_by_id = {location['id']: location for location in locations}
    valid_location_ids = locations_by_id.keys()

    for location_id in location_ids:
        if location_id not in valid_location_ids:
            raise ValueError(f'Unknown location ID {location_id}')

    all_slots = {location_id: get_slots_for_location(location_id)
                 for location_id in location_ids}

    has_slots_open = False
    for location_id, slots in all_slots.items():
        location_name = locations_by_id[location_id]['name']
        print(f'Location {location_name} (ID {location_id}) has {len(slots)} slots')
        for slot in slots:
            slot_date = slot['startTimestamp'][:10]
            if target_dates and slot_date not in target_dates:
                print(f"* {slot['startTimestamp']} - skipped (not a target date)")
                continue
            print(f"* {slot['startTimestamp']} - {slot['endTimestamp']} ({slot['duration']} minutes)")
            has_slots_open = True

    return has_slots_open

def main():
    found_appointment = False
    try:
        found_appointment = any_appointment_slots_open()
    except ValueError as ex:
        print(ex)
        exit(1)
    except Exception as ex:
        print(ex)
    finally:
        exit(1 if found_appointment else 0)

if __name__ == '__main__':
    main()
