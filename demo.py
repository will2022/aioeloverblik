import argparse
import asyncio
import os
import sys
from datetime import date, timedelta

from dotenv import load_dotenv

from aioeloverblik import EloverblikClient, EloverblikThirdPartyClient
from aioeloverblik.exceptions import EloverblikError

# Load .env
load_dotenv()


async def run_customer_demo(token):
    print("--- Customer API Demo ---")
    async with EloverblikClient(refresh_token=token) as client:
        try:
            print("Fetching metering points...")
            mps = await client.get_metering_points()
            print(f"Found {len(mps)} metering points.")

            if not mps:
                print("No metering points found.")
                return

            # Use specific ID from env if available, otherwise default to first
            env_mp_id = os.getenv("TEST_METERING_POINT_ID")
            target_mp = next((mp for mp in mps if mp.metering_point_id == env_mp_id), None) if env_mp_id else mps[0]

            mp_id = target_mp.metering_point_id
            print(f"Using Metering Point: {mp_id}")

            print(f"Fetching details for {mp_id}...")
            details = await client.get_details([mp_id])
            if details:
                print(f"Address: {details[0].street_name} {details[0].building_number}, {details[0].city_name}")

            print(f"Fetching time series for {mp_id} (last 2 days)...")
            today = date.today()
            from_date = today - timedelta(days=2)

            ts_data = await client.get_time_series([mp_id], from_date, today)
            print(f"Received {len(ts_data)} market documents.")

            if ts_data and ts_data[0].time_series:
                points = ts_data[0].time_series[0].periods[0].points
                print(f"First data point: Position {points[0].position} = {points[0].quantity} kWh")

        except EloverblikError as e:
            print(f"Error: {e}")


async def run_thirdparty_demo(token):
    print("--- ThirdParty API Demo ---")
    async with EloverblikThirdPartyClient(refresh_token=token) as client:
        try:
            print("Fetching authorizations...")
            auths = await client.get_authorizations()
            print(f"Found {len(auths)} authorizations.")

            if not auths:
                print("No authorizations found.")
                return

            # Pick the first one
            auth = auths[0]
            print(f"Using authorization for: {auth.customer_name} ({auth.customer_cvr})")

            print("Fetching metering points for this auth...")
            mps = await client.get_metering_points(scope="authorizationId", identifier=auth.authorization_id)
            print(f"Found {len(mps)} metering points.")

            if mps:
                mp_id = mps[0].metering_point_id
                print(f"Fetching time series for {mp_id}...")
                today = date.today()
                from_date = today - timedelta(days=2)
                ts_data = await client.get_time_series([mp_id], from_date, today)
                print(f"Got data: {len(ts_data)} docs")

        except EloverblikError as e:
            print(f"Error: {e}")


async def main():
    parser = argparse.ArgumentParser(description="Eloverblik API Demo")
    parser.add_argument("--mode", choices=["customer", "thirdparty"], required=True, help="API mode to test")
    parser.add_argument("--token", help="Refresh token (overrides .env)")

    args = parser.parse_args()

    token = args.token or os.getenv("ELOVERBLIK_REFRESH_TOKEN")
    if not token:
        print("Error: No refresh token provided. Set ELOVERBLIK_REFRESH_TOKEN in .env or use --token.")
        sys.exit(1)

    if args.mode == "customer":
        await run_customer_demo(token)
    elif args.mode == "thirdparty":
        await run_thirdparty_demo(token)


if __name__ == "__main__":
    asyncio.run(main())
