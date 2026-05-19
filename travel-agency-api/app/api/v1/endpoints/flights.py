from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.skyscanner_client import SkyscannerError, get_skyscanner_client

from app.schemas.price_history import (
    InsufficientDataResponse,
    PriceComparisonResponse,
    PriceHistoryResponse,
    PriceRangeResponse,
    PriceSnapshotSchema,
)
from app.services.price_history_service import (
    PriceHistoryService,
    extract_calendar_prices,
)
from app.services.skyscanner_service import SkyscannerService

router = APIRouter(prefix="/flights", tags=["flights"])


def get_skyscanner_service() -> SkyscannerService:
    return SkyscannerService(get_skyscanner_client())


def get_price_history_service(db: Session = Depends(get_db)) -> PriceHistoryService:
    return PriceHistoryService(db)


@router.get("/price-calendar", summary="Get oneway price calendar for a route")
async def get_price_calendar(
    origin_sky_id: str = Query(..., description="Origin code, e.g. LOND, SFO"),
    destination_sky_id: str = Query(..., description="Destination code, e.g. NYCA, CDG"),
    from_date: str = Query(..., description="Start date, format: YYYY-MM-DD"),
    to_date: Optional[str] = Query(None, description="End date, format: YYYY-MM-DD"),
    market: str = Query("US"),
    currency: str = Query("USD"),
    cabin_class: str = Query("economy"),
    service: SkyscannerService = Depends(get_skyscanner_service),
    history_service: PriceHistoryService = Depends(get_price_history_service),
):
    try:
        result = service.get_price_calendar(
            origin_sky_id=origin_sky_id,
            destination_sky_id=destination_sky_id,
            from_date=from_date,
            to_date=to_date,
            market=market,
            currency=currency,
            cabin_class=cabin_class,
        )
    except SkyscannerError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error

    records = extract_calendar_prices(result, origin_sky_id, destination_sky_id, currency)
    if records:
        history_service.record_many(records)

    return {"records_saved": len(records), "data": result}


@router.get("/price-calendar-return", summary="Get return trip price calendar for a route")
async def get_price_calendar_return(
    origin_sky_id: str = Query(..., description="Origin code, e.g. LOND"),
    destination_sky_id: str = Query(..., description="Destination code, e.g. NYCA"),
    from_date: str = Query(..., description="Outbound departure date, format: YYYY-MM-DD"),
    return_from_date: str = Query(..., description="Return departure date, format: YYYY-MM-DD"),
    market: str = Query("US"),
    currency: str = Query("USD"),
    service: SkyscannerService = Depends(get_skyscanner_service),
):
    try:
        return service.get_price_calendar_return(
            origin_sky_id=origin_sky_id,
            destination_sky_id=destination_sky_id,
            from_date=from_date,
            return_from_date=return_from_date,
            market=market,
            currency=currency,
        )
    except SkyscannerError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.get("/cheapest-oneway", summary="Get cheapest oneway prices for a month")
async def get_cheapest_oneway(
    origin_sky_id: str = Query(..., description="Origin code, e.g. LOND"),
    destination_sky_id: str = Query(..., description="Destination code, e.g. NYCA"),
    month: str = Query(..., description="Target month, format: YYYY-MM"),
    market: str = Query("US"),
    currency: str = Query("USD"),
    service: SkyscannerService = Depends(get_skyscanner_service),
):
    try:
        return service.get_cheapest_oneway(
            origin_sky_id=origin_sky_id,
            destination_sky_id=destination_sky_id,
            month=month,
            market=market,
            currency=currency,
        )
    except SkyscannerError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error


# ─── Historical price data ────────────────────────────────────────────────────

@router.get(
    "/price-history",
    response_model=PriceHistoryResponse,
    summary="Get stored historical price snapshots for a route",
)
async def get_price_history(
    origin_sky_id: str = Query(..., description="Origin code, e.g. SFO"),
    destination_sky_id: str = Query(..., description="Destination code, e.g. CDG"),
    departure_date: Optional[date] = Query(None, description="Filter by departure date, format: YYYY-MM-DD"),
    airline_code: Optional[str] = Query(None, description="Filter by airline code, e.g. AA"),
    from_recorded: Optional[date] = Query(None, description="Snapshots recorded on or after this date"),
    to_recorded: Optional[date] = Query(None, description="Snapshots recorded on or before this date"),
    history_service: PriceHistoryService = Depends(get_price_history_service),
):
    rows = history_service.get_history(
        origin=origin_sky_id,
        destination=destination_sky_id,
        departure_date=departure_date,
        airline_code=airline_code,
        from_recorded=from_recorded,
        to_recorded=to_recorded,
    )
    return PriceHistoryResponse(
        origin=origin_sky_id,
        destination=destination_sky_id,
        departure_date=departure_date,
        airline_code=airline_code,
        snapshots=[
            PriceSnapshotSchema(
                departure_date=r.departure_date,
                recorded_at=r.recorded_at,
                price=r.price,
                currency=r.currency,
            )
            for r in rows
        ],
        data_points=len(rows),
    )


@router.get(
    "/price-range",
    response_model=PriceRangeResponse,
    summary="Get lowest and highest recorded prices for a route",
)
async def get_price_range(
    origin_sky_id: str = Query(..., description="Origin code, e.g. SFO"),
    destination_sky_id: str = Query(..., description="Destination code, e.g. CDG"),
    departure_date: Optional[date] = Query(None, description="Filter by departure date, format: YYYY-MM-DD"),
    from_recorded: Optional[date] = Query(None),
    to_recorded: Optional[date] = Query(None),
    history_service: PriceHistoryService = Depends(get_price_history_service),
):
    result, count = history_service.get_price_range(
        origin=origin_sky_id,
        destination=destination_sky_id,
        departure_date=departure_date,
        from_recorded=from_recorded,
        to_recorded=to_recorded,
    )
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No price data found for this route. Try calling /flights/price-calendar first.",
        )
    return PriceRangeResponse(
        origin=origin_sky_id,
        destination=destination_sky_id,
        departure_date=departure_date,
        **result,
    )


@router.get(
    "/price-comparison",
    summary="Compare current price to historical average for a route (optionally filtered by airline)",
)
async def get_price_comparison(
    origin_sky_id: str = Query(..., description="Origin code, e.g. SFO"),
    destination_sky_id: str = Query(..., description="Destination code, e.g. CDG"),
    departure_date: Optional[date] = Query(None, description="Optional: filter to a specific departure date, format: YYYY-MM-DD"),
    airline_code: Optional[str] = Query(None, description="Optional: filter to a specific airline, e.g. AA"),
    history_service: PriceHistoryService = Depends(get_price_history_service),
):
    result, count = history_service.get_comparison(
        origin=origin_sky_id,
        destination=destination_sky_id,
        departure_date=departure_date,
        airline_code=airline_code,
    )
    if result is None:
        return InsufficientDataResponse(
            message="Insufficient data for this time period",
            data_points=count,
        )
    return PriceComparisonResponse(
        origin=origin_sky_id,
        destination=destination_sky_id,
        departure_date=departure_date,
        airline_code=airline_code,
        data_points=count,
        **result,
    )
