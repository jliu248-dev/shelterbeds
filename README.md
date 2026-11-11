# shelterbeds
A web app that lets caseworkers find and reserve open emergency shelter beds in real time, replacing phone calls with eligibility matching, instant holds, and automatic expiration.
## Problem 
People experiencing homelessness, and the caseworkers, volunteers, and family members helping them, often have to call shelters one by one to find an open bed. Availability changes hourly, each shelter has different rules, and beds are often gone by the time someone arrives. ShelterBeds lets shelters post live availability so people can find a bed they qualify for, request it, and know it's held for them.

## How the system starts

The first admin account is created by running a Python seed script (`seed_admin.py`) that inserts the admin directly into the PostgreSQL database on Neon. It reads the admin's email and password from environment variables (ADMIN_EMAIL, ADMIN_PASSWORD), hashes the password, and only creates the account if it doesn't already exist, so running it twice is safe.

After that:
- Seekers register through the website and can use the app right away.
- Shelter staff register through the website but start as "pending." The admin logs in, approves them, and links them to their shelter. Until then, they can't post beds.

To run it:
    python seed_admin.py