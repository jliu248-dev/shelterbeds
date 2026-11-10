"""Load real emergency shelters near Santa Clara University into the database.

    python seed_shelters.py

Safe to run more than once: shelters that already exist (same name) are skipped.

Details come from public directories (City of Santa Clara, Santa Clara County
reentry guide, shelterlistings.org and the shelters' own sites), checked
2026-11-09. Phone numbers are left out because sources disagreed; the app
tells people to call 211 or the shelter's website to confirm before going.
Domestic-violence shelters are left out on purpose: their locations are confidential.
"""
from datetime import date

from app import create_app
from app.extensions import db
from app.models import Shelter

CHECKED = date(2026, 11, 9)

SHELTERS = [
    {
        "name": "Bill Wilson Center Youth Shelter",
        "operator": "Bill Wilson Center",
        "address": "3490 The Alameda",
        "city": "Santa Clara",
        "zip_code": "95050",
        "serves": "Youth ages 11–17",
        "description": "Short-term shelter for runaway and homeless youth, with individual, "
                       "group and family counseling. About a mile from Santa Clara University.",
        "website": "https://www.billwilsoncenter.org",
    },
    {
        "name": "Boccardo Reception Center",
        "operator": "HomeFirst",
        "address": "2011 Little Orchard Street",
        "city": "San Jose",
        "zip_code": "95125",
        "serves": "Adults without minor children",
        "description": "Large 24-hour shelter for single adults (around 250 beds). "
                       "Intake is done in person.",
        "website": "https://www.homefirstscc.org",
    },
    {
        "name": "CityTeam Men's Shelter",
        "operator": "CityTeam",
        "address": "1174 Old Bayshore Highway",
        "city": "San Jose",
        "zip_code": "95112",
        "serves": "Men 18+",
        "description": "Nightly emergency shelter for men. Arrive in person in the "
                       "afternoon to get a bed; check current line-up times before going.",
        "website": "https://www.cityteam.org/get-help/san-jose",
    },
    {
        "name": "Julian Street Inn",
        "operator": "LifeMoves",
        "address": "546 West Julian Street",
        "city": "San Jose",
        "zip_code": "95110",
        "serves": "Adults with serious mental illness",
        "description": "Emergency and interim housing for adults experiencing homelessness "
                       "and serious mental illness, including veterans.",
        "website": "https://www.lifemoves.org",
    },
    {
        "name": "Georgia Travis House",
        "operator": None,
        "address": "260 Commercial Street",
        "city": "San Jose",
        "zip_code": "95112",
        "serves": "Women and children",
        "description": "Emergency shelter for women and their children.",
        "website": None,
    },
    {
        "name": "Heritage Home",
        "operator": None,
        "address": "435 North 3rd Street",
        "city": "San Jose",
        "zip_code": "95112",
        "serves": "Pregnant women",
        "description": "Residential shelter and support for pregnant women.",
        "website": None,
    },
    {
        "name": "Casa de Clara",
        "operator": "San Jose Catholic Worker",
        "address": "318 North 6th Street",
        "city": "San Jose",
        "zip_code": "95112",
        "serves": "Women and families",
        "description": "Catholic Worker house offering shelter and hospitality to women and families.",
        "website": None,
    },
]


def main():
    app = create_app()
    with app.app_context():
        added = 0
        for data in SHELTERS:
            if Shelter.query.filter_by(name=data["name"]).first():
                print(f"Skip (exists): {data['name']}")
                continue
            db.session.add(Shelter(info_checked_on=CHECKED, **data))
            added += 1
            print(f"Added: {data['name']}")
        db.session.commit()
        print(f"Done. {added} shelter(s) added.")


if __name__ == "__main__":
    main()
