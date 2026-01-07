from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseApiModel(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


# --- Common Response Structures ---


class ResponseStatus(BaseApiModel):
    success: bool
    error_code: int = Field(alias="errorCode")
    error_text: Optional[str] = Field(None, alias="errorText")
    id: Optional[str] = None
    stack_trace: Optional[str] = Field(None, alias="stackTrace")


class ApiResponse(ResponseStatus, Generic[T]):
    result: Optional[T] = None


class ListApiResponse(ResponseStatus, Generic[T]):
    result: Optional[list[T]] = None


# --- Metering Points ---


class ChildMeteringPoint(BaseApiModel):
    parent_metering_point_id: Optional[str] = Field(None, alias="parentMeteringPointId")
    metering_point_id: Optional[str] = Field(None, alias="meteringPointId")
    type_of_mp: Optional[str] = Field(None, alias="typeOfMP")
    meter_reading_occurrence: Optional[str] = Field(None, alias="meterReadingOccurrence")


class MeteringPoint(BaseApiModel):
    metering_point_id: Optional[str] = Field(None, alias="meteringPointId")
    type_of_mp: Optional[str] = Field(None, alias="typeOfMP")
    balance_supplier_name: Optional[str] = Field(None, alias="balanceSupplierName")
    street_code: Optional[str] = Field(None, alias="streetCode")
    street_name: Optional[str] = Field(None, alias="streetName")
    building_number: Optional[str] = Field(None, alias="buildingNumber")
    floor_id: Optional[str] = Field(None, alias="floorId")
    room_id: Optional[str] = Field(None, alias="roomId")
    postcode: Optional[str] = None
    city_name: Optional[str] = Field(None, alias="cityName")
    city_sub_division_name: Optional[str] = Field(None, alias="citySubDivisionName")
    municipality_code: Optional[str] = Field(None, alias="municipalityCode")
    has_relation: bool = Field(False, alias="hasRelation")
    consumer_cvr: Optional[str] = Field(None, alias="consumerCVR")
    data_access_cvr: Optional[str] = Field(None, alias="dataAccessCVR")
    child_metering_points: Optional[list[ChildMeteringPoint]] = Field(None, alias="childMeteringPoints")
    location_description: Optional[str] = Field(None, alias="locationDescription")
    meter_reading_occurrence: Optional[str] = Field(None, alias="meterReadingOccurrence")
    first_consumer_party_name: Optional[str] = Field(None, alias="firstConsumerPartyName")
    second_consumer_party_name: Optional[str] = Field(None, alias="secondConsumerPartyName")
    meter_number: Optional[str] = Field(None, alias="meterNumber")
    consumer_start_date: Optional[str] = Field(None, alias="consumerStartDate")


class MeteringPointDetail(MeteringPoint):
    parent_metering_point_id: Optional[str] = Field(None, alias="parentMeteringPointId")
    grid_operator_name: Optional[str] = Field(None, alias="gridOperatorName")
    grid_operator_id: Optional[str] = Field(None, alias="gridOperatorID")
    production_obligation: Optional[str] = Field(None, alias="productionObligation")
    mp_capacity: Optional[str] = Field(None, alias="mpCapacity")
    mp_connection_type: Optional[str] = Field(None, alias="mpConnectionType")
    disconnection_type: Optional[str] = Field(None, alias="disconnectionType")
    product: Optional[str] = Field(None, alias="product")
    asset_type: Optional[str] = Field(None, alias="assetType")


# --- Charges / Tariffs ---


class Charge(BaseApiModel):
    name: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    valid_from_date: Optional[str] = Field(None, alias="validFromDate")
    valid_to_date: Optional[str] = Field(None, alias="validToDate")
    period_type: Optional[str] = Field(None, alias="periodType")
    price: Optional[float] = None
    quantity: Optional[int] = None


class TariffPrice(BaseApiModel):
    position: Optional[str] = None
    price: Optional[float] = None


class Tariff(Charge):
    prices: Optional[list[TariffPrice]] = None


class MeteringPointCharges(BaseApiModel):
    metering_point_id: Optional[str] = Field(None, alias="meteringPointId")
    subscriptions: Optional[list[Charge]] = None
    tariffs: Optional[list[Tariff]] = None
    fees: Optional[list[Charge]] = None


# --- Time Series ---


class Point(BaseApiModel):
    position: Optional[str] = None
    quantity: Optional[str] = Field(None, alias="out_Quantity.quantity")
    quality: Optional[str] = Field(None, alias="out_Quantity.quality")


class TimeInterval(BaseApiModel):
    start: Optional[str] = None
    end: Optional[str] = None


class Period(BaseApiModel):
    resolution: Optional[str] = None
    time_interval: Optional[TimeInterval] = Field(None, alias="timeInterval")
    points: Optional[list[Point]] = Field(None, alias="Point")


class MarketEvaluationPoint(BaseApiModel):
    mrid: Optional[dict] = Field(None, alias="mRID")


class TimeSeries(BaseApiModel):
    mrid: Optional[str] = Field(None, alias="mRID")
    business_type: Optional[str] = Field(None, alias="businessType")
    curve_type: Optional[str] = Field(None, alias="curveType")
    measurement_unit_name: Optional[str] = Field(None, alias="measurement_Unit.name")
    periods: Optional[list[Period]] = Field(None, alias="Period")


class MyEnergyDataMarketDocument(BaseApiModel):
    mrid: Optional[str] = Field(None, alias="mRID")
    created_date_time: Optional[str] = Field(None, alias="createdDateTime")
    sender_name: Optional[str] = Field(None, alias="sender_MarketParticipant.name")
    time_series: Optional[list[TimeSeries]] = Field(None, alias="TimeSeries")


class MyEnergyDataResponse(ResponseStatus):
    result: Optional[list[MyEnergyDataMarketDocument]] = Field(None, alias="MyEnergyData_MarketDocument")


class TimeSeriesResult(BaseApiModel):
    market_document: Optional[MyEnergyDataMarketDocument] = Field(None, alias="MyEnergyData_MarketDocument")


# --- Third Party ---


class Authorization(BaseApiModel):
    authorization_id: Optional[str] = Field(None, alias="id")
    third_party_name: Optional[str] = Field(None, alias="thirdPartyName")
    valid_from: Optional[str] = Field(None, alias="validFrom")
    valid_to: Optional[str] = Field(None, alias="validTo")
    customer_name: Optional[str] = Field(None, alias="customerName")
    customer_cvr: Optional[str] = Field(None, alias="customerCVR")
    customer_key: Optional[str] = Field(None, alias="customerKey")
    include_future_metering_points: bool = Field(False, alias="includeFutureMeteringPoints")
