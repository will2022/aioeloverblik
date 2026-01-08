from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseApiModel(BaseModel):
    """Base model for all API models with common configuration."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


# --- Common Response Structures ---


class ResponseStatus(BaseApiModel):
    """Base response status from the API."""

    success: bool
    error_code: int = Field(alias="errorCode")
    error_text: Optional[str] = Field(None, alias="errorText")
    id: Optional[str] = None
    stack_trace: Optional[str] = Field(None, alias="stackTrace")


class ApiResponse(ResponseStatus, Generic[T]):
    """Generic response wrapper for a single result object."""

    result: Optional[T] = None


class ListApiResponse(ResponseStatus, Generic[T]):
    """Generic response wrapper for a list of result objects."""

    result: Optional[list[T]] = None


# --- Metering Points ---


class ContactAddress(BaseApiModel):
    """Detailed contact address information.

    Attributes:
        address_code: Code specifying the type of contact address.
            Possible values: D01 (Technical address), D04 (Juridical address).
        street_name: Street name.
        building_number: Building number.
        floor_id: Floor id.
        room_id: Room id.
        postcode: Postcode.
        city_name: City name.
        country_name: Country name.
        contact_phone_number: Contact phone number.
        contact_mobile_number: Contact mobile number.
        contact_email_address: Contact e-mail address.
        attention: Specifies if there a person or a c/o address to attention.
        post_box: Specifies if there a postbox to attention.
        protected_address: Specifies if the Address is protected.
    """

    contact_name_1: Optional[str] = Field(None, alias="contactName1")
    contact_name_2: Optional[str] = Field(None, alias="contactName2")
    address_code: Optional[str] = Field(None, alias="addressCode")
    street_name: Optional[str] = Field(None, alias="streetName")
    building_number: Optional[str] = Field(None, alias="buildingNumber")
    floor_id: Optional[str] = Field(None, alias="floorId")
    room_id: Optional[str] = Field(None, alias="roomId")
    city_sub_division_name: Optional[str] = Field(None, alias="citySubDivisionName")
    postcode: Optional[str] = None
    city_name: Optional[str] = Field(None, alias="cityName")
    country_name: Optional[str] = Field(None, alias="countryName")
    contact_phone_number: Optional[str] = Field(None, alias="contactPhoneNumber")
    contact_mobile_number: Optional[str] = Field(None, alias="contactMobileNumber")
    contact_email_address: Optional[str] = Field(None, alias="contactEmailAddress")
    attention: Optional[str] = None
    post_box: Optional[str] = Field(None, alias="postBox")
    protected_address: Optional[str] = Field(None, alias="protectedAddress")


class ChildMeteringPoint(BaseApiModel):
    """Details about a child metering point.

    Attributes:
        parent_metering_point_id: The id of the related parent metering point.
        metering_point_id: Unique metering point id consisting of 18 characters.
        type_of_mp: Specifies the type of metering point.
        meter_reading_occurrence: Specifies the meter reading resolution.
        meter_number: Meter number identifying the physical meter.
    """

    parent_metering_point_id: Optional[str] = Field(None, alias="parentMeteringPointId")
    metering_point_id: Optional[str] = Field(None, alias="meteringPointId")
    type_of_mp: Optional[str] = Field(None, alias="typeOfMP")
    meter_reading_occurrence: Optional[str] = Field(None, alias="meterReadingOccurrence")
    meter_number: Optional[str] = Field(None, alias="meterNumber")


class MeteringPointBase(BaseApiModel):
    """Base information about a metering point shared between list and details.

    Attributes:
        metering_point_id: Unique metering point id consisting of 18 characters.
        type_of_mp: Specifies the type of metering point.
            Examples: E17 (Consumption), E18 (Production).
        balance_supplier_name: Name of the balance supplier.
        street_code: Street code.
        street_name: Street name.
        building_number: Building number.
        floor_id: Floor id.
        room_id: Room id.
        postcode: Postcode.
        city_name: City name.
        municipality_code: Municipality code.
        consumer_cvr: CVR number of the registered consumer (business only).
        data_access_cvr: Additional CVR number of the registered consumer (business only).
        child_metering_points: List of child metering points.
        location_description: Description of the location.
        meter_reading_occurrence: Specifies the meter reading resolution.
            Values: ANDET (Other), P1M (Monthly), PT15M (15 Minutes), PT1H (Hourly).
        settlement_method: Settlement method of the metering point.
            Values: D01 (Flex settled), E01 (Profiled settled), E02 (Non-profiled settled).
        meter_number: Meter number identifying the physical meter.
        consumer_start_date: Date when the current consumer was registered (UTC).
    """

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
    consumer_cvr: Optional[str] = Field(None, alias="consumerCVR")
    data_access_cvr: Optional[str] = Field(None, alias="dataAccessCVR")
    child_metering_points: Optional[list[ChildMeteringPoint]] = Field(None, alias="childMeteringPoints")
    location_description: Optional[str] = Field(None, alias="locationDescription")
    meter_reading_occurrence: Optional[str] = Field(None, alias="meterReadingOccurrence")
    settlement_method: Optional[str] = Field(None, alias="settlementMethod")
    first_consumer_party_name: Optional[str] = Field(None, alias="firstConsumerPartyName")
    second_consumer_party_name: Optional[str] = Field(None, alias="secondConsumerPartyName")
    meter_number: Optional[str] = Field(None, alias="meterNumber")
    consumer_start_date: Optional[str] = Field(None, alias="consumerStartDate")


class MeteringPoint(MeteringPointBase):
    """Basic information about a metering point (List View - Customer API).

    Attributes:
        has_relation: Indicates if there is a relation.
    """

    has_relation: bool = Field(False, alias="hasRelation")


class MeteringPointThirdParty(MeteringPointBase):
    """Basic information about a metering point (List View - ThirdParty API).

    Attributes:
        access_from: Start date of access delegation.
        access_to: End date of access delegation.
    """

    access_from: Optional[str] = Field(None, alias="accessFrom")
    access_to: Optional[str] = Field(None, alias="accessTo")


class MeteringPointDetail(MeteringPointBase):
    """Extended detailed information about a metering point.

    Attributes:
        parent_metering_point_id: The id of the related parent metering point.
        grid_operator_name: Name of the grid operator.
        grid_operator_id: Id of the Grid Operator.
        production_obligation: Specifies if a production obligation applies.
        mp_capacity: Power in kW for the production facility.
        mp_connection_type: Connection type (D01: Direct, D02: Installation).
        disconnection_type: Disconnection type (D01: Remote, D02: Manual).
        product: Product Id (e.g., Active power, Reactive power).
        asset_type: Energy type (e.g., D11: Photovoltaics, D12: Wind turbines).
        energy_time_series_measure_unit: Energy measurement unit (e.g., KWH).
        estimated_annual_volume: Estimated annual consumption/production.
        metering_grid_area_identification: Id of the grid area.
        net_settlement_group: Net settlement group (0-99).
        physical_status_of_mp: Physical status (D03: New, E22: Connected, E23: Disconnected).
        consumer_category: Consumer category code.
        power_limit_kw: Max power limit in kW.
        power_limit_a: Max current limit in Ampere.
        sub_type_of_mp: Sub type (D01: Physical, D02: Virtual, D03: Calculated).
        mp_address_wash_instructions: Address wash instruction (D01: Washable, D02: Not washable).
        dar_reference: Reference id to the public Danish Address Register.
        balance_supplier_id: Id of the Balance Supplier.
        balance_supplier_start_date: Start date for the balance supplier.
        mp_reading_characteristics: Reading type (D01: Automatic, D02: Manual).
        meter_counter_digits: Number of digits on the meter.
        meter_counter_multiply_factor: Conversion factor for the meter.
        meter_counter_unit: Unit for the meter counter.
        meter_counter_type: Counter type (D01: Accumulated, D02: Balanced).
        mp_relation_type: Not used. No value is returned. Will be removed in a later version.
        occurrence: Date of the data request.
        tax_reduction: Indicates entitlement to electricity tax reduction.
        tax_settlement_date: Date for tax reduction commencement/termination.
    """

    parent_metering_point_id: Optional[str] = Field(None, alias="parentMeteringPointId")
    grid_operator_name: Optional[str] = Field(None, alias="gridOperatorName")
    grid_operator_id: Optional[str] = Field(None, alias="gridOperatorID")
    production_obligation: Optional[str] = Field(None, alias="productionObligation")
    mp_capacity: Optional[str] = Field(None, alias="mpCapacity")
    mp_connection_type: Optional[str] = Field(None, alias="mpConnectionType")
    disconnection_type: Optional[str] = Field(None, alias="disconnectionType")
    product: Optional[str] = Field(None, alias="product")
    asset_type: Optional[str] = Field(None, alias="assetType")
    energy_time_series_measure_unit: Optional[str] = Field(None, alias="energyTimeSeriesMeasureUnit")
    estimated_annual_volume: Optional[str] = Field(None, alias="estimatedAnnualVolume")
    metering_grid_area_identification: Optional[str] = Field(None, alias="meteringGridAreaIdentification")
    net_settlement_group: Optional[str] = Field(None, alias="netSettlementGroup")
    physical_status_of_mp: Optional[str] = Field(None, alias="physicalStatusOfMP")
    consumer_category: Optional[str] = Field(None, alias="consumerCategory")
    power_limit_kw: Optional[str] = Field(None, alias="powerLimitKW")
    power_limit_kw_decimal: Optional[float] = Field(None, alias="powerLimitKWDecimal")
    power_limit_a: Optional[str] = Field(None, alias="powerLimitA")
    sub_type_of_mp: Optional[str] = Field(None, alias="subTypeOfMP")
    mp_address_wash_instructions: Optional[str] = Field(None, alias="mpAddressWashInstructions")
    dar_reference: Optional[str] = Field(None, alias="darReference")
    contact_addresses: Optional[list[ContactAddress]] = Field(None, alias="contactAddresses")
    balance_supplier_id: Optional[str] = Field(None, alias="balanceSupplierId")
    balance_supplier_start_date: Optional[str] = Field(None, alias="balanceSupplierStartDate")
    balance_supplier_id_scheme_agency_identifier: Optional[str] = Field(
        None,
        alias="balanceSupplierId_SchemeAgencyIdentifier",
    )
    protected_name: Optional[str] = Field(None, alias="protectedName")
    grid_operator_id_scheme_agency_identifier: Optional[str] = Field(
        None,
        alias="gridOperatorID_SchemeAgencyIdentifier",
    )
    metering_point_alias: Optional[str] = Field(None, alias="meteringPointAlias")
    mp_reading_characteristics: Optional[str] = Field(None, alias="mpReadingCharacteristics")
    meter_counter_digits: Optional[str] = Field(None, alias="meterCounterDigits")
    meter_counter_multiply_factor: Optional[str] = Field(None, alias="meterCounterMultiplyFactor")
    meter_counter_unit: Optional[str] = Field(None, alias="meterCounterUnit")
    meter_counter_type: Optional[str] = Field(None, alias="meterCounterType")
    mp_relation_type: Optional[str] = Field(None, alias="mpRelationType")
    occurrence: Optional[str] = Field(None, alias="occurrence")
    tax_reduction: Optional[str] = Field(None, alias="taxReduction")
    tax_settlement_date: Optional[str] = Field(None, alias="taxSettlementDate")


# --- Charges / Tariffs ---


class BaseCharge(BaseApiModel):
    """Base model for charges and tariffs.

    Attributes:
        name: Name of the fee.
        description: Description of the fee.
        owner: GLN (Global Location Number) representing the owner (grid operator).
        valid_from_date: Date the fee starts.
        valid_to_date: Date the fee ends.
        period_type: Type of period "DAY" or "HOUR".
    """

    name: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    valid_from_date: Optional[str] = Field(None, alias="validFromDate")
    valid_to_date: Optional[str] = Field(None, alias="validToDate")
    period_type: Optional[str] = Field(None, alias="periodType")


class Charge(BaseCharge):
    """Represents a fee, subscription, or other charge.

    Attributes:
        price: Price of the subscription in dkkr.
        quantity: Quantity of the subscription.
    """

    price: Optional[float] = None
    quantity: Optional[int] = None


class TariffPrice(BaseApiModel):
    """Price information for a specific tariff position.

    Attributes:
        position: Hour of tariff.
        price: Price of the tariff in dkkr.
    """

    position: Optional[str] = None
    price: Optional[float] = None


class Tariff(BaseCharge):
    """Tariff information extending standard Charge details with prices.

    Attributes:
        prices: List of prices per hour/period for the tariff.
    """

    prices: Optional[list[TariffPrice]] = None


class MeteringPointCharges(BaseApiModel):
    """Subscriptions, tariffs, and fees for a metering point.

    Attributes:
        metering_point_id: Id of the metering point.
        subscriptions: List of subscriptions for the metering point.
        tariffs: List of tariffs for the metering point.
        fees: List of fees for the metering point.
    """

    metering_point_id: Optional[str] = Field(None, alias="meteringPointId")
    subscriptions: Optional[list[Charge]] = None
    tariffs: Optional[list[Tariff]] = None
    fees: Optional[list[Charge]] = None


# --- Time Series ---


class Point(BaseApiModel):
    """Single data point in a time series (quantity/quality).

    Attributes:
        position: Position in the period (e.g., 1-96 for 15m intervals).
        quantity: The quantity value (kWh/m3/etc) with max 3 decimals.
        quality: Quality of the measurement.
            Values: A01 (Adjusted), A02 (Not available), A03 (Estimated), A04 (Measured), A05 (Incomplete).
    """

    position: Optional[str] = None
    quantity: Optional[str] = Field(None, alias="out_Quantity.quantity")
    quality: Optional[str] = Field(None, alias="out_Quantity.quality")


class TimeInterval(BaseApiModel):
    """Start and end time for a period.

    Attributes:
        start: Start date of period (UTC ISO 8601).
        end: End date of period (UTC ISO 8601).
    """

    start: Optional[str] = None
    end: Optional[str] = None


class Period(BaseApiModel):
    """Time period containing multiple data points.

    Attributes:
        resolution: Species the resolution of the period.
            Values: PT15M (15 min), PT1H (Hour), P1D (Day), P1M (Month), P1Y (Year).
        time_interval: The time interval covered.
        points: The list of measurement points.
    """

    resolution: Optional[str] = None
    time_interval: Optional[TimeInterval] = Field(None, alias="timeInterval")
    points: Optional[list[Point]] = Field(None, alias="Point")


class MarketEvaluationMeteringPoint(BaseApiModel):
    """Details about the market evaluation metering point.

    Attributes:
        coding_scheme: Coding scheme used (Fixed value: A10 for GSRN).
        name: Unique metering point id (18 chars).
    """

    coding_scheme: Optional[str] = Field(None, alias="codingScheme")
    name: Optional[str] = None


class MarketEvaluationPoint(BaseApiModel):
    """Wrapper for market evaluation point details."""

    mrid: Optional[MarketEvaluationMeteringPoint] = Field(None, alias="mRID")


class TimeSeries(BaseApiModel):
    """Time series data including periods and points.

    Attributes:
        mrid: Unique metering point id.
        business_type: Nature of the time series.
            Values: A01 (Production), A04 (Consumption), A64 (Consumption - profiled).
        curve_type: Type of curve (Always A01 for valid series).
        measurement_unit_name: Unit of measure (e.g., KWH).
        periods: List of periods containing data points.
        market_evaluation_point: Market evaluation point identification.
    """

    mrid: Optional[str] = Field(None, alias="mRID")
    business_type: Optional[str] = Field(None, alias="businessType")
    curve_type: Optional[str] = Field(None, alias="curveType")
    measurement_unit_name: Optional[str] = Field(None, alias="measurement_Unit.name")
    periods: Optional[list[Period]] = Field(None, alias="Period")
    market_evaluation_point: Optional[MarketEvaluationPoint] = Field(None, alias="MarketEvaluationPoint")


class MyEnergyDataMarketDocument(BaseApiModel):
    """Market document containing time series data.

    Attributes:
        mrid: Unique ID of the market document.
        created_date_time: Creation date/time (UTC ISO 8601).
        sender_name: Sender name (Fixed: Energinet).
        time_series: List of time series data.
    """

    mrid: Optional[str] = Field(None, alias="mRID")
    created_date_time: Optional[str] = Field(None, alias="createdDateTime")
    sender_name: Optional[str] = Field(None, alias="sender_MarketParticipant.name")
    time_series: Optional[list[TimeSeries]] = Field(None, alias="TimeSeries")


class MyEnergyDataResponse(ResponseStatus):
    """Response wrapper specifically for MyEnergyData."""

    result: Optional[list[MyEnergyDataMarketDocument]] = Field(None, alias="MyEnergyData_MarketDocument")


class TimeSeriesResult(BaseApiModel):
    """Wrapper for a Time Series result."""

    market_document: Optional[MyEnergyDataMarketDocument] = Field(None, alias="MyEnergyData_MarketDocument")


# --- Third Party ---


class AuthorizationDto(BaseApiModel):
    """Data object for a third-party authorization (Power of Attorney).

    Attributes:
        authorization_id: Identifier UUID of this power of attorney.
        third_party_name: Name of the third party owning this power of attorney.
        valid_from: The earliest date allowed to request data on.
        valid_to: Max date allowed to request data on.
        customer_name: Name of the customer extracted from the customer's NemID certificate.
        customer_cvr: CVR number of the customer.
        customer_key: Optional key applied to the authorization (can be used to identify customer).
        include_future_metering_points: Whether future metering points are automatically included.
        time_stamp: Date and time when the authorization was registered (UTC ISO 8601).
    """

    authorization_id: Optional[str] = Field(None, alias="id")
    third_party_name: Optional[str] = Field(None, alias="thirdPartyName")
    valid_from: Optional[str] = Field(None, alias="validFrom")
    valid_to: Optional[str] = Field(None, alias="validTo")
    customer_name: Optional[str] = Field(None, alias="customerName")
    customer_cvr: Optional[str] = Field(None, alias="customerCVR")
    customer_key: Optional[str] = Field(None, alias="customerKey")
    include_future_metering_points: bool = Field(False, alias="includeFutureMeteringPoints")
    time_stamp: Optional[str] = Field(None, alias="timeStamp")
