"""
Tool execution: maps MCP tool names to SAP API_PRODUCT_SRV OData GET calls.

Field validation: $select values are checked against the exact field lists from
OP_API_PRODUCT_SRV_0001.json before the request is sent.  An invalid field name
returns a descriptive error so the AI agent can self-correct without a round-trip
to S/4HANA.
"""

from __future__ import annotations

from typing import Any

from sap_destination import SAPDestinationClient

# ---------------------------------------------------------------------------
# Valid $select fields per tool (derived from OP_API_PRODUCT_SRV_0001.json)
# Navigation properties (to_*) are included so $expand works correctly.
# ---------------------------------------------------------------------------
_VALID_SELECT: dict[str, frozenset[str]] = {
    "list_products": frozenset({
        "Product","ProductType","CrossPlantStatus","CrossPlantStatusValidityDate",
        "CreationDate","CreatedByUser","LastChangeDate","LastChangedByUser",
        "LastChangeDateTime","IsMarkedForDeletion","ProductOldID","GrossWeight",
        "PurchaseOrderQuantityUnit","SourceOfSupply","WeightUnit","NetWeight",
        "CountryOfOrigin","CompetitorID","ProductGroup","BaseUnit",
        "ItemCategoryGroup","ProductHierarchy","Division","VarblPurOrdUnitIsActive",
        "VolumeUnit","MaterialVolume","ANPCode","Brand","ProcurementRule",
        "ValidityStartDate","LowLevelCode","ProdNoInGenProdInPrepackProd",
        "SerialIdentifierAssgmtProfile","SizeOrDimensionText","IndustryStandardName",
        "ProductStandardID","InternationalArticleNumberCat","ProductIsConfigurable",
        "IsBatchManagementRequired","ExternalProductGroup","CrossPlantConfigurableProduct",
        "SerialNoExplicitnessLevel","ProductManufacturerNumber","ManufacturerNumber",
        "ManufacturerPartProfile","QltyMgmtInProcmtIsActive","IndustrySector",
        "ChangeNumber","MaterialRevisionLevel","HandlingIndicator","WarehouseProductGroup",
        "WarehouseStorageCondition","StandardHandlingUnitType","SerialNumberProfile",
        "AdjustmentProfile","PreferredUnitOfMeasure","IsPilferable",
        "IsRelevantForHzdsSubstances","QuarantinePeriod","TimeUnitForQuarantinePeriod",
        "QualityInspectionGroup","AuthorizationGroup","DocumentIsCreatedByCAD",
        "HandlingUnitType","HasVariableTareWeight","MaximumPackagingLength",
        "MaximumPackagingWidth","MaximumPackagingHeight","UnitForMaxPackagingDimensions",
        "to_Description","to_Plant","to_ProductBasicText","to_ProductInspectionText",
        "to_ProductProcurement","to_ProductPurchaseText","to_ProductQualityMgmt",
        "to_ProductSales","to_ProductSalesTax","to_ProductStorage",
        "to_ProductUnitsOfMeasure","to_SalesDelivery","to_Valuation",
    }),
    "list_product_descriptions": frozenset({"Product","Language","ProductDescription"}),
    "list_product_basic_texts": frozenset({"Product","Language","LongText"}),
    "list_product_inspection_texts": frozenset({"Product","Language","LongText"}),
    "list_product_procurement": frozenset({
        "Product","PurchaseOrderQuantityUnit","VarblPurOrdUnitStatus","PurchasingAcknProfile",
    }),
    "list_product_purchase_texts": frozenset({"Product","Language","LongText"}),
    "list_product_quality_mgmt": frozenset({"Product","QltyMgmtInProcmtIsActive"}),
    "list_product_sales": frozenset({
        "Product","SalesStatus","SalesStatusValidityDate","TaxClassification","TransportationGroup",
    }),
    "list_product_storage": frozenset({
        "Product","StorageConditions","TemperatureConditionInd","HazardousMaterialNumber",
        "NmbrOfGROrGISlipsToPrintQty","LabelType","LabelForm","MinRemainingShelfLife",
        "ExpirationDate","ShelfLifeExpirationDatePeriod","TotalShelfLife","BaseUnit",
    }),
    "list_product_plants": frozenset({
        "Product","Plant","PurchasingGroup","CountryOfOrigin","RegionOfOrigin",
        "ProductionInvtryManagedLoc","ProfileCode","ProfileValidityStartDate",
        "AvailabilityCheckType","FiscalYearVariant","PeriodType","ProfitCenter",
        "Commodity","GoodsReceiptDuration","MaintenanceStatusName","IsMarkedForDeletion",
        "MRPType","MRPResponsible","ABCIndicator","MinimumLotSizeQuantity",
        "MaximumLotSizeQuantity","FixedLotSizeQuantity","ConsumptionTaxCtrlCode",
        "IsCoProduct","ProductIsConfigurable","StockDeterminationGroup",
        "StockInTransferQuantity","StockInTransitQuantity","HasPostToInspectionStock",
        "IsBatchManagementRequired","SerialNumberProfile","IsNegativeStockAllowed",
        "GoodsReceiptBlockedStockQty","HasConsignmentCtrl","FiscalYearCurrentPeriod",
        "FiscalMonthCurrentPeriod","ProcurementType","IsInternalBatchManaged",
        "ProductCFOPCategory","ProductIsExciseTaxRelevant","BaseUnit",
        "ConfigurableProduct","GoodsIssueUnit","MaterialFreightGroup",
        "OriginalBatchReferenceMaterial","OriglBatchManagementIsRequired",
        "ProductIsCriticalPrt","ProductLogisticsHandlingGroup",
        "to_PlantMRPArea","to_PlantQualityMgmt","to_PlantSales","to_PlantStorage",
        "to_PlantText","to_ProdPlantInternationalTrade","to_ProductPlantCosting",
        "to_ProductPlantForecast","to_ProductPlantProcurement","to_ProductSupplyPlanning",
        "to_ProductWorkScheduling","to_StorageLocation",
    }),
    "list_product_plant_costing": frozenset({
        "Product","Plant","IsCoProduct","CostingLotSize","VarianceKey","BaseUnit",
        "TaskListGroupCounter","TaskListGroup","TaskListType","CostingProductionVersion",
        "IsFixedPriceCoProduct","CostingSpecialProcurementType","SourceBOMAlternative",
        "ProductBOMUsage","ProductIsCostingRelevant",
    }),
    "list_product_plant_forecasting": frozenset({
        "Product","Plant","ConsumptionRefUsageEndDate","ConsumptionQtyMultiplier",
        "ConsumptionReferenceProduct","ConsumptionReferencePlant",
    }),
    "list_product_plant_intl_trade": frozenset({
        "Product","Plant","CountryOfOrigin","RegionOfOrigin","ConsumptionTaxCtrlCode",
        "ProductCASNumber","ProdIntlTradeClassification","ExportAndImportProductGroup",
    }),
    "list_product_plant_mrp_areas": frozenset({
        "Product","Plant","MRPArea","MRPType","MRPResponsible","MRPGroup",
        "ReorderThresholdQuantity","PlanningTimeFence","LotSizingProcedure",
        "LotSizeRoundingQuantity","MinimumLotSizeQuantity","MaximumLotSizeQuantity",
        "MaximumStockQuantity","AssemblyScrapPercent","ProcurementSubType",
        "DfltStorageLocationExtProcmt","MRPPlanningCalendar","SafetyStockQuantity",
        "RangeOfCvrgPrflCode","SafetyDuration","FixedLotSizeQuantity",
        "LotSizeIndependentCosts","IsStorageCosts","RqmtQtyRcptTaktTmeInWrkgDays",
        "SrvcLvl","IsMarkedForDeletion","PerdPrflForSftyTme","IsMRPDependentRqmt",
        "IsSafetyTime","PlannedDeliveryDurationInDays","IsPlannedDeliveryTime",
        "Currency","BaseUnit","PlanAndOrderDayDetermination","RoundingProfile","StorageLocation",
    }),
    "list_product_plant_procurement": frozenset({
        "Product","Plant","IsAutoPurOrdCreationAllowed","IsSourceListRequired",
        "SourceOfSupplyCategory","ItmIsRlvtToJITDelivSchedules",
    }),
    "list_product_plant_quality_mgmt": frozenset({
        "Product","Plant","MaximumStoragePeriod","QualityMgmtCtrlKey",
        "MatlQualityAuthorizationGroup","HasPostToInspectionStock",
        "InspLotDocumentationIsRequired","SuplrQualityManagementSystem",
        "RecrrgInspIntervalTimeInDays","ProductQualityCertificateType",
    }),
    "list_product_plant_sales": frozenset({
        "Product","Plant","LoadingGroup","ReplacementPartType",
        "CapPlanningQuantityInBaseUoM","ProductShippingProcessingTime",
        "WrkCentersShipgSetupTimeInDays","AvailabilityCheckType","BaseUnit",
    }),
    "list_product_plant_storage": frozenset({
        "Product","Plant","InventoryForCycleCountInd","ProvisioningServiceLevel",
        "CycleCountingIndicatorIsFixed","ProdMaximumStoragePeriodUnit",
        "WrhsMgmtPtwyAndStkRemovalStrgy",
    }),
    "list_product_plant_texts": frozenset({"Product","Plant","LongText"}),
    "list_product_sales_delivery": frozenset({
        "Product","ProductSalesOrg","ProductDistributionChnl","MinimumOrderQuantity",
        "SupplyingPlant","PriceSpecificationProductGroup","AccountDetnProductGroup",
        "DeliveryNoteProcMinDelivQty","ItemCategoryGroup","DeliveryQuantityUnit",
        "DeliveryQuantity","ProductSalesStatus","ProductSalesStatusValidityDate",
        "SalesMeasureUnit","IsMarkedForDeletion","ProductHierarchy",
        "FirstSalesSpecProductGroup","SecondSalesSpecProductGroup",
        "ThirdSalesSpecProductGroup","FourthSalesSpecProductGroup",
        "FifthSalesSpecProductGroup","MinimumMakeToOrderOrderQty","BaseUnit",
        "LogisticsStatisticsGroup","VolumeRebateGroup","ProductCommissionGroup",
        "CashDiscountIsDeductible","PricingReferenceProduct","RoundingProfile",
        "ProductUnitGroup","VariableSalesUnitIsNotAllowed",
        "ProductHasAttributeID01","ProductHasAttributeID02","ProductHasAttributeID03",
        "ProductHasAttributeID04","ProductHasAttributeID05","ProductHasAttributeID06",
        "ProductHasAttributeID07","ProductHasAttributeID08","ProductHasAttributeID09",
        "ProductHasAttributeID10","to_SalesTax","to_SalesText",
    }),
    "list_product_sales_tax": frozenset({"Product","Country","TaxCategory","TaxClassification"}),
    "list_product_sales_texts": frozenset({
        "Product","ProductSalesOrg","ProductDistributionChnl","Language","LongText",
    }),
    "list_product_storage_locations": frozenset({
        "Product","Plant","StorageLocation","WarehouseStorageBin","MaintenanceStatus",
        "PhysicalInventoryBlockInd","CreationDate","IsMarkedForDeletion",
        "DateOfLastPostedCntUnRstrcdStk","InventoryCorrectionFactor",
        "InvtryRestrictedUseStockInd","InvtryCurrentYearStockInd",
        "InvtryQualInspCurrentYrStkInd","InventoryBlockStockInd",
        "InvtryRestStockPrevPeriodInd","InventoryStockPrevPeriod",
        "InvtryStockQltyInspPrevPeriod","HasInvtryBlockStockPrevPeriod",
        "FiscalYearCurrentPeriod","FiscalMonthCurrentPeriod",
        "FiscalYearCurrentInvtryPeriod","LeanWrhsManagementPickingArea",
    }),
    "list_product_supply_planning": frozenset({
        "Product","Plant","FixedLotSizeQuantity","MaximumLotSizeQuantity",
        "MinimumLotSizeQuantity","LotSizeRoundingQuantity","LotSizingProcedure",
        "MRPType","MRPResponsible","SafetyStockQuantity","MinimumSafetyStockQuantity",
        "PlanningTimeFence","ABCIndicator","MaximumStockQuantity","ReorderThresholdQuantity",
        "PlannedDeliveryDurationInDays","SafetyDuration","PlanningStrategyGroup",
        "TotalReplenishmentLeadTime","ProcurementType","ProcurementSubType",
        "AssemblyScrapPercent","AvailabilityCheckType","GoodsReceiptDuration",
        "MRPGroup","DfltStorageLocationExtProcmt","ProdRqmtsConsumptionMode",
        "BackwardCnsmpnPeriodInWorkDays","FwdConsumptionPeriodInWorkDays","BaseUnit",
        "PlanAndOrderDayDetermination","RoundingProfile","LotSizeIndependentCosts",
        "MRPPlanningCalendar","RangeOfCvrgPrflCode","IsSafetyTime","PerdPrflForSftyTme",
        "IsMRPDependentRqmt","InHouseProductionTime","ProductIsForCrossProject",
        "StorageCostsPercentageCode","SrvcLvl","MRPAvailabilityType","FollowUpProduct",
        "RepetitiveManufacturingIsAllwd","DependentRequirementsType","IsBulkMaterialComponent",
        "RepetitiveManufacturingProfile","RqmtQtyRcptTaktTmeInWrkgDays",
        "ForecastRequirementsAreSplit","EffectiveOutDate","MRPProfile",
        "ComponentScrapInPercent","ProductIsToBeDiscontinued","ProdRqmtsAreConsolidated",
        "MatlCompIsMarkedForBackflush","ProposedProductSupplyArea","Currency",
        "PlannedOrderActionControl",
    }),
    "list_product_units_of_measure": frozenset({
        "Product","AlternativeUnit","QuantityNumerator","QuantityDenominator",
        "MaterialVolume","VolumeUnit","GrossWeight","WeightUnit",
        "GlobalTradeItemNumber","GlobalTradeItemNumberCategory",
        "UnitSpecificProductLength","UnitSpecificProductWidth","UnitSpecificProductHeight",
        "ProductMeasurementUnit","LowerLevelPackagingUnit","RemainingVolumeAfterNesting",
        "MaximumStackingFactor","CapacityUsage","BaseUnit","to_InternationalArticleNumber",
    }),
    "list_product_ean_codes": frozenset({
        "Product","AlternativeUnit","ConsecutiveNumber","ProductStandardID",
        "InternationalArticleNumberCat","IsMainGlobalTradeItemNumber",
    }),
    "list_product_valuations": frozenset({
        "Product","ValuationArea","ValuationType","ValuationClass",
        "PriceDeterminationControl","StandardPrice","PriceUnitQty",
        "InventoryValuationProcedure","IsMarkedForDeletion","MovingAveragePrice",
        "ValuationCategory","ProductUsageType","ProductOriginType","IsProducedInhouse",
        "ProdCostEstNumber","ProjectStockValuationClass","ValuationClassSalesOrderStock",
        "PlannedPrice1InCoCodeCrcy","PlannedPrice2InCoCodeCrcy","PlannedPrice3InCoCodeCrcy",
        "FuturePlndPrice1ValdtyDate","FuturePlndPrice2ValdtyDate","FuturePlndPrice3ValdtyDate",
        "TaxBasedPricesPriceUnitQty","PriceLastChangeDate","PlannedPrice",
        "PrevInvtryPriceInCoCodeCrcy","Currency","BaseUnit",
        "to_MLAccount","to_MLPrices","to_ValuationAccount","to_ValuationCosting",
    }),
    "list_product_valuation_accounts": frozenset({
        "Product","ValuationArea","ValuationType","CurrencyRole","Currency",
        "ProductPriceControl","PriceUnitQty","MovingAveragePrice","StandardPrice",
    }),
    "list_product_valuation_costing": frozenset({
        "Product","ValuationArea","ValuationType","CurrencyRole","Currency",
        "FuturePrice","FuturePriceValidityStartDate","PlannedPrice",
    }),
    "list_product_ml_accounts": frozenset({
        "Product","ValuationArea","ValuationType","CurrencyRole","Currency",
        "ProductPriceControl","PriceUnitQty","MovingAveragePrice","StandardPrice",
    }),
    "list_product_ml_prices": frozenset({
        "Product","ValuationArea","ValuationType","CurrencyRole","Currency",
        "FuturePrice","FuturePriceValidityStartDate","PlannedPrice",
    }),
    "list_product_work_scheduling": frozenset({
        "Product","Plant","MaterialBaseQuantity","UnlimitedOverDelivIsAllowed",
        "OverDelivToleranceLimit","UnderDelivToleranceLimit","ProductionInvtryManagedLoc",
        "BaseUnit","ProductProcessingTime","ProductionSupervisor",
        "ProductProductionQuantityUnit","ProdnOrderIsBatchRequired",
        "TransitionMatrixProductsGroup","OrderChangeManagementProfile",
        "MatlCompIsMarkedForBackflush","SetupAndTeardownTime",
        "ProductionSchedulingProfile","TransitionTime",
    }),
}

# get_* tools share the same valid fields as their list_* counterparts
_VALID_SELECT["get_product"] = _VALID_SELECT["list_products"]
_VALID_SELECT["get_product_description"] = _VALID_SELECT["list_product_descriptions"]
_VALID_SELECT["get_product_basic_text"] = _VALID_SELECT["list_product_basic_texts"]
_VALID_SELECT["get_product_inspection_text"] = _VALID_SELECT["list_product_inspection_texts"]
_VALID_SELECT["get_product_procurement"] = _VALID_SELECT["list_product_procurement"]
_VALID_SELECT["get_product_purchase_text"] = _VALID_SELECT["list_product_purchase_texts"]
_VALID_SELECT["get_product_quality_mgmt"] = _VALID_SELECT["list_product_quality_mgmt"]
_VALID_SELECT["get_product_sales"] = _VALID_SELECT["list_product_sales"]
_VALID_SELECT["get_product_storage"] = _VALID_SELECT["list_product_storage"]
_VALID_SELECT["get_product_plant"] = _VALID_SELECT["list_product_plants"]
_VALID_SELECT["get_product_plant_costing"] = _VALID_SELECT["list_product_plant_costing"]
_VALID_SELECT["get_product_plant_forecasting"] = _VALID_SELECT["list_product_plant_forecasting"]
_VALID_SELECT["get_product_plant_intl_trade"] = _VALID_SELECT["list_product_plant_intl_trade"]
_VALID_SELECT["get_product_plant_mrp_area"] = _VALID_SELECT["list_product_plant_mrp_areas"]
_VALID_SELECT["get_product_plant_procurement"] = _VALID_SELECT["list_product_plant_procurement"]
_VALID_SELECT["get_product_plant_quality_mgmt"] = _VALID_SELECT["list_product_plant_quality_mgmt"]
_VALID_SELECT["get_product_plant_sales"] = _VALID_SELECT["list_product_plant_sales"]
_VALID_SELECT["get_product_plant_storage"] = _VALID_SELECT["list_product_plant_storage"]
_VALID_SELECT["get_product_plant_text"] = _VALID_SELECT["list_product_plant_texts"]
_VALID_SELECT["get_product_sales_delivery"] = _VALID_SELECT["list_product_sales_delivery"]
_VALID_SELECT["get_product_sales_tax"] = _VALID_SELECT["list_product_sales_tax"]
_VALID_SELECT["get_product_sales_text"] = _VALID_SELECT["list_product_sales_texts"]
_VALID_SELECT["get_product_storage_location"] = _VALID_SELECT["list_product_storage_locations"]
_VALID_SELECT["get_product_supply_planning"] = _VALID_SELECT["list_product_supply_planning"]
_VALID_SELECT["get_product_unit_of_measure"] = _VALID_SELECT["list_product_units_of_measure"]
_VALID_SELECT["get_product_ean_code"] = _VALID_SELECT["list_product_ean_codes"]
_VALID_SELECT["get_product_valuation"] = _VALID_SELECT["list_product_valuations"]
_VALID_SELECT["get_product_valuation_account"] = _VALID_SELECT["list_product_valuation_accounts"]
_VALID_SELECT["get_product_valuation_costing"] = _VALID_SELECT["list_product_valuation_costing"]
_VALID_SELECT["get_product_ml_account"] = _VALID_SELECT["list_product_ml_accounts"]
_VALID_SELECT["get_product_ml_price"] = _VALID_SELECT["list_product_ml_prices"]
_VALID_SELECT["get_product_work_scheduling"] = _VALID_SELECT["list_product_work_scheduling"]


def _validate_select(tool_name: str, params: dict) -> None:
    """
    Validate $select field names against the OData spec.

    Raises ValueError with a helpful message listing valid fields if any
    requested field is not in the spec for this entity.
    """
    select_str = params.get("$select")
    if not select_str:
        return

    valid = _VALID_SELECT.get(tool_name)
    if not valid:
        return  # no whitelist for this tool — pass through

    requested = {f.strip() for f in select_str.split(",") if f.strip()}
    invalid = requested - valid
    if invalid:
        sorted_valid = sorted(valid - {f for f in valid if f.startswith("to_")})
        raise ValueError(
            f"Invalid $select field(s) for {tool_name}: {sorted(invalid)}. "
            f"Valid fields are: {sorted_valid}"
        )


def _odata_params(args: dict) -> dict:
    """Extract OData system query options from tool arguments."""
    mapping = {
        "top": "$top",
        "skip": "$skip",
        "filter": "$filter",
        "select": "$select",
        "orderby": "$orderby",
        "expand": "$expand",
        "search": "$search",
        "inlinecount": "$inlinecount",
    }
    return {v: args[k] for k, v in mapping.items() if args.get(k) is not None}


def execute_tool(sap: SAPDestinationClient, name: str, args: dict) -> Any:
    """
    Dispatch a tool call to the appropriate S/4HANA OData GET endpoint.

    Args:
        sap:  Configured SAPDestinationClient instance.
        name: MCP tool name.
        args: Tool arguments from the MCP client.

    Returns:
        Parsed JSON response from S/4HANA.

    Raises:
        ValueError: if the tool name is unknown or $select contains invalid fields.
        requests.HTTPError: on non-2xx S/4HANA responses.
    """
    p = _odata_params(args)
    _validate_select(name, p)

    # ------------------------------------------------------------------
    # A_Product
    # ------------------------------------------------------------------
    if name == "list_products":
        return sap.get("/A_Product", p)

    if name == "get_product":
        prod = args["product"]
        return sap.get(f"/A_Product('{prod}')", p)

    # ------------------------------------------------------------------
    # A_ProductDescription
    # ------------------------------------------------------------------
    if name == "list_product_descriptions":
        return sap.get("/A_ProductDescription", p)

    if name == "get_product_description":
        prod, lang = args["product"], args["language"]
        return sap.get(f"/A_ProductDescription(Product='{prod}',Language='{lang}')", p)

    # ------------------------------------------------------------------
    # A_ProductBasicText
    # ------------------------------------------------------------------
    if name == "list_product_basic_texts":
        return sap.get("/A_ProductBasicText", p)

    if name == "get_product_basic_text":
        prod, lang = args["product"], args["language"]
        return sap.get(f"/A_ProductBasicText(Product='{prod}',Language='{lang}')", p)

    # ------------------------------------------------------------------
    # A_ProductInspectionText
    # ------------------------------------------------------------------
    if name == "list_product_inspection_texts":
        return sap.get("/A_ProductInspectionText", p)

    if name == "get_product_inspection_text":
        prod, lang = args["product"], args["language"]
        return sap.get(f"/A_ProductInspectionText(Product='{prod}',Language='{lang}')", p)

    # ------------------------------------------------------------------
    # A_ProductProcurement
    # ------------------------------------------------------------------
    if name == "list_product_procurement":
        return sap.get("/A_ProductProcurement", p)

    if name == "get_product_procurement":
        prod = args["product"]
        return sap.get(f"/A_ProductProcurement('{prod}')", p)

    # ------------------------------------------------------------------
    # A_ProductPurchaseText
    # ------------------------------------------------------------------
    if name == "list_product_purchase_texts":
        return sap.get("/A_ProductPurchaseText", p)

    if name == "get_product_purchase_text":
        prod, lang = args["product"], args["language"]
        return sap.get(f"/A_ProductPurchaseText(Product='{prod}',Language='{lang}')", p)

    # ------------------------------------------------------------------
    # A_ProductQualityMgmt
    # ------------------------------------------------------------------
    if name == "list_product_quality_mgmt":
        return sap.get("/A_ProductQualityMgmt", p)

    if name == "get_product_quality_mgmt":
        prod = args["product"]
        return sap.get(f"/A_ProductQualityMgmt('{prod}')", p)

    # ------------------------------------------------------------------
    # A_ProductSales
    # ------------------------------------------------------------------
    if name == "list_product_sales":
        return sap.get("/A_ProductSales", p)

    if name == "get_product_sales":
        prod = args["product"]
        return sap.get(f"/A_ProductSales('{prod}')", p)

    # ------------------------------------------------------------------
    # A_ProductStorage
    # ------------------------------------------------------------------
    if name == "list_product_storage":
        return sap.get("/A_ProductStorage", p)

    if name == "get_product_storage":
        prod = args["product"]
        return sap.get(f"/A_ProductStorage('{prod}')", p)

    # ------------------------------------------------------------------
    # A_ProductPlant
    # ------------------------------------------------------------------
    if name == "list_product_plants":
        return sap.get("/A_ProductPlant", p)

    if name == "get_product_plant":
        prod, plant = args["product"], args["plant"]
        return sap.get(f"/A_ProductPlant(Product='{prod}',Plant='{plant}')", p)

    # ------------------------------------------------------------------
    # A_ProductPlantCosting
    # ------------------------------------------------------------------
    if name == "list_product_plant_costing":
        return sap.get("/A_ProductPlantCosting", p)

    if name == "get_product_plant_costing":
        prod, plant = args["product"], args["plant"]
        return sap.get(f"/A_ProductPlantCosting(Product='{prod}',Plant='{plant}')", p)

    # ------------------------------------------------------------------
    # A_ProductPlantForecasting
    # ------------------------------------------------------------------
    if name == "list_product_plant_forecasting":
        return sap.get("/A_ProductPlantForecasting", p)

    if name == "get_product_plant_forecasting":
        prod, plant = args["product"], args["plant"]
        return sap.get(f"/A_ProductPlantForecasting(Product='{prod}',Plant='{plant}')", p)

    # ------------------------------------------------------------------
    # A_ProductPlantIntlTrd
    # ------------------------------------------------------------------
    if name == "list_product_plant_intl_trade":
        return sap.get("/A_ProductPlantIntlTrd", p)

    if name == "get_product_plant_intl_trade":
        prod, plant = args["product"], args["plant"]
        return sap.get(f"/A_ProductPlantIntlTrd(Product='{prod}',Plant='{plant}')", p)

    # ------------------------------------------------------------------
    # A_ProductPlantMRPArea
    # ------------------------------------------------------------------
    if name == "list_product_plant_mrp_areas":
        return sap.get("/A_ProductPlantMRPArea", p)

    if name == "get_product_plant_mrp_area":
        prod, plant, mrp = args["product"], args["plant"], args["mrp_area"]
        return sap.get(
            f"/A_ProductPlantMRPArea(Product='{prod}',Plant='{plant}',MRPArea='{mrp}')", p
        )

    # ------------------------------------------------------------------
    # A_ProductPlantProcurement
    # ------------------------------------------------------------------
    if name == "list_product_plant_procurement":
        return sap.get("/A_ProductPlantProcurement", p)

    if name == "get_product_plant_procurement":
        prod, plant = args["product"], args["plant"]
        return sap.get(f"/A_ProductPlantProcurement(Product='{prod}',Plant='{plant}')", p)

    # ------------------------------------------------------------------
    # A_ProductPlantQualityMgmt
    # ------------------------------------------------------------------
    if name == "list_product_plant_quality_mgmt":
        return sap.get("/A_ProductPlantQualityMgmt", p)

    if name == "get_product_plant_quality_mgmt":
        prod, plant = args["product"], args["plant"]
        return sap.get(f"/A_ProductPlantQualityMgmt(Product='{prod}',Plant='{plant}')", p)

    # ------------------------------------------------------------------
    # A_ProductPlantSales
    # ------------------------------------------------------------------
    if name == "list_product_plant_sales":
        return sap.get("/A_ProductPlantSales", p)

    if name == "get_product_plant_sales":
        prod, plant = args["product"], args["plant"]
        return sap.get(f"/A_ProductPlantSales(Product='{prod}',Plant='{plant}')", p)

    # ------------------------------------------------------------------
    # A_ProductPlantStorage
    # ------------------------------------------------------------------
    if name == "list_product_plant_storage":
        return sap.get("/A_ProductPlantStorage", p)

    if name == "get_product_plant_storage":
        prod, plant = args["product"], args["plant"]
        return sap.get(f"/A_ProductPlantStorage(Product='{prod}',Plant='{plant}')", p)

    # ------------------------------------------------------------------
    # A_ProductPlantText
    # ------------------------------------------------------------------
    if name == "list_product_plant_texts":
        return sap.get("/A_ProductPlantText", p)

    if name == "get_product_plant_text":
        prod, plant = args["product"], args["plant"]
        return sap.get(f"/A_ProductPlantText(Product='{prod}',Plant='{plant}')", p)

    # ------------------------------------------------------------------
    # A_ProductSalesDelivery
    # ------------------------------------------------------------------
    if name == "list_product_sales_delivery":
        return sap.get("/A_ProductSalesDelivery", p)

    if name == "get_product_sales_delivery":
        prod = args["product"]
        sorg = args["sales_org"]
        dchnl = args["distribution_channel"]
        return sap.get(
            f"/A_ProductSalesDelivery(Product='{prod}',"
            f"ProductSalesOrg='{sorg}',ProductDistributionChnl='{dchnl}')",
            p,
        )

    # ------------------------------------------------------------------
    # A_ProductSalesTax
    # ------------------------------------------------------------------
    if name == "list_product_sales_tax":
        return sap.get("/A_ProductSalesTax", p)

    if name == "get_product_sales_tax":
        prod = args["product"]
        country = args["country"]
        tax_cat = args["tax_category"]
        tax_cls = args["tax_classification"]
        return sap.get(
            f"/A_ProductSalesTax(Product='{prod}',Country='{country}',"
            f"TaxCategory='{tax_cat}',TaxClassification='{tax_cls}')",
            p,
        )

    # ------------------------------------------------------------------
    # A_ProductSalesText
    # ------------------------------------------------------------------
    if name == "list_product_sales_texts":
        return sap.get("/A_ProductSalesText", p)

    if name == "get_product_sales_text":
        prod = args["product"]
        sorg = args["sales_org"]
        dchnl = args["distribution_channel"]
        lang = args["language"]
        return sap.get(
            f"/A_ProductSalesText(Product='{prod}',ProductSalesOrg='{sorg}',"
            f"ProductDistributionChnl='{dchnl}',Language='{lang}')",
            p,
        )

    # ------------------------------------------------------------------
    # A_ProductStorageLocation
    # ------------------------------------------------------------------
    if name == "list_product_storage_locations":
        return sap.get("/A_ProductStorageLocation", p)

    if name == "get_product_storage_location":
        prod, plant, sloc = args["product"], args["plant"], args["storage_location"]
        return sap.get(
            f"/A_ProductStorageLocation(Product='{prod}',Plant='{plant}',"
            f"StorageLocation='{sloc}')",
            p,
        )

    # ------------------------------------------------------------------
    # A_ProductSupplyPlanning
    # ------------------------------------------------------------------
    if name == "list_product_supply_planning":
        return sap.get("/A_ProductSupplyPlanning", p)

    if name == "get_product_supply_planning":
        prod, plant = args["product"], args["plant"]
        return sap.get(f"/A_ProductSupplyPlanning(Product='{prod}',Plant='{plant}')", p)

    # ------------------------------------------------------------------
    # A_ProductUnitsOfMeasure
    # ------------------------------------------------------------------
    if name == "list_product_units_of_measure":
        return sap.get("/A_ProductUnitsOfMeasure", p)

    if name == "get_product_unit_of_measure":
        prod, unit = args["product"], args["alternative_unit"]
        return sap.get(
            f"/A_ProductUnitsOfMeasure(Product='{prod}',AlternativeUnit='{unit}')", p
        )

    # ------------------------------------------------------------------
    # A_ProductUnitsOfMeasureEAN (GTIN)
    # ------------------------------------------------------------------
    if name == "list_product_ean_codes":
        return sap.get("/A_ProductUnitsOfMeasureEAN", p)

    if name == "get_product_ean_code":
        prod = args["product"]
        unit = args["alternative_unit"]
        seq = args["consecutive_number"]
        return sap.get(
            f"/A_ProductUnitsOfMeasureEAN(Product='{prod}',AlternativeUnit='{unit}',"
            f"ConsecutiveNumber='{seq}')",
            p,
        )

    # ------------------------------------------------------------------
    # A_ProductValuation
    # ------------------------------------------------------------------
    if name == "list_product_valuations":
        return sap.get("/A_ProductValuation", p)

    if name == "get_product_valuation":
        prod = args["product"]
        varea = args["valuation_area"]
        vtype = args["valuation_type"]
        return sap.get(
            f"/A_ProductValuation(Product='{prod}',ValuationArea='{varea}',"
            f"ValuationType='{vtype}')",
            p,
        )

    # ------------------------------------------------------------------
    # A_ProductValuationAccount
    # ------------------------------------------------------------------
    if name == "list_product_valuation_accounts":
        return sap.get("/A_ProductValuationAccount", p)

    if name == "get_product_valuation_account":
        prod = args["product"]
        varea = args["valuation_area"]
        vtype = args["valuation_type"]
        return sap.get(
            f"/A_ProductValuationAccount(Product='{prod}',ValuationArea='{varea}',"
            f"ValuationType='{vtype}')",
            p,
        )

    # ------------------------------------------------------------------
    # A_ProductValuationCosting (mapped to A_ProductMLPrices in spec)
    # ------------------------------------------------------------------
    if name == "list_product_valuation_costing":
        return sap.get("/A_ProductMLPrices", p)

    if name == "get_product_valuation_costing":
        prod = args["product"]
        varea = args["valuation_area"]
        vtype = args["valuation_type"]
        return sap.get(
            f"/A_ProductMLPrices(Product='{prod}',ValuationArea='{varea}',"
            f"ValuationType='{vtype}')",
            p,
        )

    # ------------------------------------------------------------------
    # A_ProductMLAccount
    # ------------------------------------------------------------------
    if name == "list_product_ml_accounts":
        return sap.get("/A_ProductMLAccount", p)

    if name == "get_product_ml_account":
        prod = args["product"]
        varea = args["valuation_area"]
        vtype = args["valuation_type"]
        crole = args["currency_role"]
        return sap.get(
            f"/A_ProductMLAccount(Product='{prod}',ValuationArea='{varea}',"
            f"ValuationType='{vtype}',CurrencyRole='{crole}')",
            p,
        )

    # ------------------------------------------------------------------
    # A_ProductMLPrices
    # ------------------------------------------------------------------
    if name == "list_product_ml_prices":
        return sap.get("/A_ProductMLPrices", p)

    if name == "get_product_ml_price":
        prod = args["product"]
        varea = args["valuation_area"]
        vtype = args["valuation_type"]
        crole = args["currency_role"]
        return sap.get(
            f"/A_ProductMLPrices(Product='{prod}',ValuationArea='{varea}',"
            f"ValuationType='{vtype}',CurrencyRole='{crole}')",
            p,
        )

    # ------------------------------------------------------------------
    # A_ProductWorkScheduling
    # ------------------------------------------------------------------
    if name == "list_product_work_scheduling":
        return sap.get("/A_ProductWorkScheduling", p)

    if name == "get_product_work_scheduling":
        prod, plant = args["product"], args["plant"]
        return sap.get(f"/A_ProductWorkScheduling(Product='{prod}',Plant='{plant}')", p)

    raise ValueError(f"Unknown tool: {name!r}")
