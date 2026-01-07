# aioeloverblik

[![PyPI version](https://badge.fury.io/py/aioeloverblik.svg)](https://badge.fury.io/py/aioeloverblik)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://github.com/will2022/aioeloverblik/actions/workflows/publish.yml/badge.svg)](https://github.com/will2022/aioeloverblik/actions)

**Async Python wrapper for the Eloverblik.dk API.**

Supports both:
- **Customer API**: Access your own electricity data (metering points, charges, time series).
- **ThirdParty API**: Access data via authorization scopes (for apps/services).

Built with `httpx` and `pydantic` for robustness and type safety.

## Resources
- [Customer API Docs](https://api.eloverblik.dk/customerapi/index.html)
- [ThirdParty API Docs](https://api.eloverblik.dk/ThirdPartyApi/index.html)
- [ElOverblik Data Portal (Get Tokens)](https://eloverblik.dk/)

## Installation

```bash
pip install aioeloverblik
```

## Usage

### Customer API (Own Data)

```python
import asyncio
from aioeloverblik import EloverblikClient

async def main():
    async with EloverblikClient(refresh_token="YOUR_TOKEN") as client:
        # Get metering points
        mps = await client.get_metering_points()
        if mps:
            mp_id = mps[0].metering_point_id
            
            # Get time series data (last 3 days)
            from datetime import date, timedelta
            today = date.today()
            from_date = today - timedelta(days=3)
            
            ts_data = await client.get_time_series([mp_id], from_date, today, aggregation="Hour")
            print(f"Got {len(ts_data)} market documents")
            
            for doc in ts_data:
                for series in doc.time_series:
                    for period in series.periods:
                        for point in period.points:
                            print(f"Time: {point.position}, Value: {point.quantity} {series.measurement_unit_name}")

asyncio.run(main())
```

### ThirdParty API

```python
import asyncio
from aioeloverblik import EloverblikThirdPartyClient

async def main():
    async with EloverblikThirdPartyClient(refresh_token="YOUR_TOKEN") as client:
        auths = await client.get_authorizations()
        print(auths)

asyncio.run(main())
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](LICENSE)
