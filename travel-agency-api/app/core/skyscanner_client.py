from functools import lru_cache
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import get_settings


class SkyscannerError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class SkyscannerClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def search_flights(
        self,
        origin_sky_id: str,
        origin_entity_id: str,
        destination_sky_id: str,
        destination_entity_id: str,
        date: str,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        cabin_class: str = "economy",
        currency: str = "USD",
        market: str = "US",
        return_date: str | None = None,
    ):
        querystring = {
            "originSkyId": origin_sky_id,
            "originEntityId": origin_entity_id,
            "destinationSkyId": destination_sky_id,
            "destinationEntityId": destination_entity_id,
            "date": date,
            "adults": str(adults),
            "childrens": str(children),
            "infants": str(infants),
            "cabinClass": cabin_class,
            "currency": currency,
            "market": market,
        }
        if return_date:
            querystring["return_date"] = return_date
        return self._get("flights/searchFlights", querystring)

    def get_price_calendar(
        self,
        origin_sky_id: str,
        destination_sky_id: str,
        from_date: str,
        to_date: str | None = None,
        market: str = "US",
        currency: str = "USD",
        cabin_class: str = "economy",
    ):
        params = {
            "originSkyId": origin_sky_id,
            "destinationSkyId": destination_sky_id,
            "fromDate": from_date,
            "market": market,
            "currency": currency,
            "cabinClass": cabin_class,
        }
        if to_date:
            params["toDate"] = to_date
        return self._get("flights/getPriceCalendar", params)

    def get_price_calendar_return(
        self,
        origin_sky_id: str,
        destination_sky_id: str,
        from_date: str,
        return_from_date: str,
        market: str = "US",
        currency: str = "USD",
    ):
        return self._get("flights/getPriceCalendarReturn", {
            "originSkyId": origin_sky_id,
            "destinationSkyId": destination_sky_id,
            "fromDate": from_date,
            "returnFromDate": return_from_date,
            "market": market,
            "currency": currency,
        })

    def get_cheapest_oneway(
        self,
        origin_sky_id: str,
        destination_sky_id: str,
        month: str,
        market: str = "US",
        currency: str = "USD",
    ):
        return self._get("flights/getCheapestOneway", {
            "originSkyId": origin_sky_id,
            "destinationSkyId": destination_sky_id,
            "month": month,
            "market": market,
            "currency": currency,
        })

    def _get(self, path: str, params: dict[str, str]):
        host = "skyscanner-flights-travel-api.p.rapidapi.com"
        request = Request(
            f"https://{host}/{path}?{urlencode(params)}",
            headers={
                "x-rapidapi-host": host,
                "x-rapidapi-key": self.api_key,
                "Content-Type": "application/json",
            },
            method="GET",
        )
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise SkyscannerError(error.code, detail or str(error)) from error
        except URLError as error:
            raise SkyscannerError(500, "Failed to connect to Skyscanner API.") from error
        except Exception as error:
            raise SkyscannerError(500, f"Unexpected error: {type(error).__name__}: {str(error)}")


@lru_cache(maxsize=1)
def get_skyscanner_client() -> SkyscannerClient:
    settings = get_settings()
    if not settings.rapidapi_key:
        raise SkyscannerError(500, "RAPIDAPI_KEY is not configured.")
    return SkyscannerClient(api_key=settings.rapidapi_key)
