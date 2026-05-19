from app.core.skyscanner_client import SkyscannerClient


class SkyscannerService:
    def __init__(self, client: SkyscannerClient) -> None:
        self.client = client

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
        return self.client.search_flights(
            origin_sky_id=origin_sky_id,
            origin_entity_id=origin_entity_id,
            destination_sky_id=destination_sky_id,
            destination_entity_id=destination_entity_id,
            date=date,
            adults=adults,
            children=children,
            infants=infants,
            cabin_class=cabin_class,
            currency=currency,
            market=market,
            return_date=return_date,
        )

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
        return self.client.get_price_calendar(
            origin_sky_id=origin_sky_id,
            destination_sky_id=destination_sky_id,
            from_date=from_date,
            to_date=to_date,
            market=market,
            currency=currency,
            cabin_class=cabin_class,
        )

    def get_price_calendar_return(
        self,
        origin_sky_id: str,
        destination_sky_id: str,
        from_date: str,
        return_from_date: str,
        market: str = "US",
        currency: str = "USD",
    ):
        return self.client.get_price_calendar_return(
            origin_sky_id=origin_sky_id,
            destination_sky_id=destination_sky_id,
            from_date=from_date,
            return_from_date=return_from_date,
            market=market,
            currency=currency,
        )

    def get_cheapest_oneway(
        self,
        origin_sky_id: str,
        destination_sky_id: str,
        month: str,
        market: str = "US",
        currency: str = "USD",
    ):
        return self.client.get_cheapest_oneway(
            origin_sky_id=origin_sky_id,
            destination_sky_id=destination_sky_id,
            month=month,
            market=market,
            currency=currency,
        )
