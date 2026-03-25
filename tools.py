"""MCP tool definitions for SAP API_PRODUCT_SRV GET endpoints."""

_LIST_PARAMS = {
    "top": {
        "type": "integer",
        "description": "Limit the number of returned records ($top). Example: 10",
    },
    "skip": {
        "type": "integer",
        "description": "Skip the first N records ($skip). Example: 20",
    },
    "filter": {
        "type": "string",
        "description": (
            "OData $filter expression. Use field names exactly as returned by the API. "
            "Examples: \"ProductType eq 'FERT'\", \"IsMarkedForDeletion eq false\", "
            "\"Plant eq '1010' and MRPType eq 'PD'\""
        ),
    },
    "select": {
        "type": "string",
        "description": (
            "Comma-separated list of fields to return ($select). "
            "Use exact API field names. Example: \"Product,ProductType,BaseUnit\""
        ),
    },
    "orderby": {
        "type": "string",
        "description": "Field(s) to sort by ($orderby). Example: \"Product asc\"",
    },
    "expand": {
        "type": "string",
        "description": (
            "Navigation properties to inline ($expand). "
            "Example: \"to_Description,to_Plant,to_ProductUnitsOfMeasure\""
        ),
    },
}

_SINGLE_PARAMS = {
    "select": _LIST_PARAMS["select"],
    "expand": _LIST_PARAMS["expand"],
}

TOOLS = [
    # ------------------------------------------------------------------
    # A_Product
    # ------------------------------------------------------------------
    {
        "name": "list_products",
        "description": (
            "Returns product master records from SAP S/4HANA (entity: A_Product). "
            "Key fields: Product (product number), ProductType (FERT=finished, HALB=semi-finished, "
            "ROH=raw material, HAWA=trading goods, DIEN=service), BaseUnit, ProductGroup, Division, "
            "GrossWeight, NetWeight, WeightUnit, Volume, VolumeUnit, ProductHierarchy, "
            "IsMarkedForDeletion, CreationDate, LastChangeDate, IndustrySector, "
            "SizeOrDimensionText, ProductStandardID (GTIN/EAN). "
            "Filter examples: \"ProductType eq 'FERT'\", \"IsMarkedForDeletion eq false\", "
            "\"ProductGroup eq '01'\". "
            "Expand navigation: to_Description, to_Plant, to_ProductUnitsOfMeasure, "
            "to_SalesDelivery, to_Valuation."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product",
        "description": (
            "Returns a single product master record by product number (A_Product). "
            "Returns all header-level fields: ProductType, BaseUnit, ProductGroup, Division, "
            "GrossWeight, NetWeight, WeightUnit, Volume, VolumeUnit, ProductHierarchy, "
            "IsMarkedForDeletion, CreationDate, LastChangeDate, IndustrySector, "
            "SizeOrDimensionText, ProductStandardID."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number, e.g. 'TG11'."},
                **_SINGLE_PARAMS,
            },
            "required": ["product"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductDescription
    # ------------------------------------------------------------------
    {
        "name": "list_product_descriptions",
        "description": (
            "Returns product descriptions for all languages (entity: A_ProductDescription). "
            "Key fields: Product, Language (e.g. 'EN', 'DE', 'FR'), ProductDescription (the text). "
            "Filter examples: \"Language eq 'EN'\", \"Product eq 'TG11'\"."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_description",
        "description": (
            "Returns the description text of a product in a specific language (A_ProductDescription). "
            "Returns: Product, Language, ProductDescription."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "language": {"type": "string", "description": "Language key, e.g. 'EN', 'DE'."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "language"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductBasicText
    # ------------------------------------------------------------------
    {
        "name": "list_product_basic_texts",
        "description": (
            "Returns basic data long texts for products (entity: A_ProductBasicText). "
            "Key fields: Product, Language, LongText. "
            "Filter example: \"Language eq 'EN'\"."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_basic_text",
        "description": (
            "Returns the basic data long text for a product in a specific language (A_ProductBasicText). "
            "Returns: Product, Language, LongText."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "language": {"type": "string", "description": "Language key, e.g. 'EN'."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "language"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductInspectionText
    # ------------------------------------------------------------------
    {
        "name": "list_product_inspection_texts",
        "description": (
            "Returns quality inspection long texts for products (entity: A_ProductInspectionText). "
            "Key fields: Product, Language, LongText."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_inspection_text",
        "description": (
            "Returns the quality inspection long text for a product in a specific language "
            "(A_ProductInspectionText). Returns: Product, Language, LongText."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "language": {"type": "string", "description": "Language key, e.g. 'EN'."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "language"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductProcurement
    # ------------------------------------------------------------------
    {
        "name": "list_product_procurement",
        "description": (
            "Returns client-level procurement data for products (entity: A_ProductProcurement). "
            "Key fields: Product, PurchaseOrderQuantityUnit, VarblPurOrdUnitIsActive, "
            "PurchasingAcknProfile."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_procurement",
        "description": (
            "Returns client-level procurement data for a specific product (A_ProductProcurement). "
            "Returns: Product, PurchaseOrderQuantityUnit, VarblPurOrdUnitIsActive, "
            "PurchasingAcknProfile."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                **_SINGLE_PARAMS,
            },
            "required": ["product"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductPurchaseText
    # ------------------------------------------------------------------
    {
        "name": "list_product_purchase_texts",
        "description": (
            "Returns purchasing long texts for products (entity: A_ProductPurchaseText). "
            "Key fields: Product, Language, LongText."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_purchase_text",
        "description": (
            "Returns the purchasing long text for a product in a specific language "
            "(A_ProductPurchaseText). Returns: Product, Language, LongText."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "language": {"type": "string", "description": "Language key, e.g. 'EN'."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "language"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductQualityMgmt
    # ------------------------------------------------------------------
    {
        "name": "list_product_quality_mgmt",
        "description": (
            "Returns client-level quality management data for products (entity: A_ProductQualityMgmt). "
            "Key fields: Product, QltyMgmtInProcmtIsActive, HasPostToInspectionStock, "
            "InspLotDocumentationIsRequired, SuplrQualityManagementSystem, "
            "RecrrgInspIntervalTimeInDays, ProductQualityCertificateType."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_quality_mgmt",
        "description": (
            "Returns client-level quality management data for a specific product "
            "(A_ProductQualityMgmt). Returns: Product, QltyMgmtInProcmtIsActive, "
            "HasPostToInspectionStock, InspLotDocumentationIsRequired, "
            "SuplrQualityManagementSystem, RecrrgInspIntervalTimeInDays, "
            "ProductQualityCertificateType."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                **_SINGLE_PARAMS,
            },
            "required": ["product"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductSales
    # ------------------------------------------------------------------
    {
        "name": "list_product_sales",
        "description": (
            "Returns client-level sales data for products (entity: A_ProductSales). "
            "Key fields: Product, SalesStatus, SalesStatusValidityDate, "
            "TransportationGroup, LoadingGroup."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_sales",
        "description": (
            "Returns client-level sales data for a specific product (A_ProductSales). "
            "Returns: Product, SalesStatus, SalesStatusValidityDate, "
            "TransportationGroup, LoadingGroup."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                **_SINGLE_PARAMS,
            },
            "required": ["product"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductStorage
    # ------------------------------------------------------------------
    {
        "name": "list_product_storage",
        "description": (
            "Returns client-level storage/warehouse data for products (entity: A_ProductStorage). "
            "Key fields: Product, StorageConditions, TemperatureConditionInd, "
            "HazardousMaterialNumber, NmbrOfGROrGISlips, LabelType, LabelForm."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_storage",
        "description": (
            "Returns client-level storage/warehouse data for a specific product (A_ProductStorage). "
            "Returns: Product, StorageConditions, TemperatureConditionInd, "
            "HazardousMaterialNumber, NmbrOfGROrGISlips, LabelType, LabelForm."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                **_SINGLE_PARAMS,
            },
            "required": ["product"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductPlant
    # ------------------------------------------------------------------
    {
        "name": "list_product_plants",
        "description": (
            "Returns plant-level data for products (entity: A_ProductPlant). "
            "Key fields: Product, Plant, ProfitCenter, GoodsReceiptDuration, "
            "AvailabilityCheckType, IsMarkedForDeletion, IsConfigurableProduct, "
            "ProcurementType (E=in-house, F=external, X=both), "
            "SpecialProcurementType, ProductionSchedulingProfile, "
            "SerialNumberProfile, MaximumStoragePeriod. "
            "Filter examples: \"Plant eq '1010'\", \"ProcurementType eq 'F'\", "
            "\"IsMarkedForDeletion eq false\"."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_plant",
        "description": (
            "Returns plant-level data for a specific product and plant (A_ProductPlant). "
            "Returns: Product, Plant, ProfitCenter, GoodsReceiptDuration, "
            "AvailabilityCheckType, ProcurementType, SpecialProcurementType, "
            "IsMarkedForDeletion, ProductionSchedulingProfile, SerialNumberProfile."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "plant": {"type": "string", "description": "Plant code, e.g. '1010'."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "plant"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductPlantCosting
    # ------------------------------------------------------------------
    {
        "name": "list_product_plant_costing",
        "description": (
            "Returns costing data for products at plant level (entity: A_ProductPlantCosting). "
            "Key fields: Product, Plant, IsCoProduct, IsBulkMaterialComponent, "
            "CostingLotSize, CostingLotSizeUnit, TaskListGroup, TaskListGroupCounter, "
            "CostingSpecialProcurementType, VarianceKey, CostingProductionVersion."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_plant_costing",
        "description": (
            "Returns costing data for a specific product and plant (A_ProductPlantCosting). "
            "Returns: Product, Plant, IsCoProduct, IsBulkMaterialComponent, "
            "CostingLotSize, CostingLotSizeUnit, VarianceKey, CostingProductionVersion."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "plant": {"type": "string", "description": "Plant code."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "plant"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductPlantForecasting
    # ------------------------------------------------------------------
    {
        "name": "list_product_plant_forecasting",
        "description": (
            "Returns consumption-based forecasting data for products at plant level "
            "(entity: A_ProductPlantForecasting). "
            "Key fields: Product, Plant, ConsumptionRefUsageStartDate, "
            "ConsumptionQtyMultiplier, ConsumptionReferenceProduct, "
            "ConsumptionReferenceProductPlant."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_plant_forecasting",
        "description": (
            "Returns forecasting data for a specific product and plant "
            "(A_ProductPlantForecasting). "
            "Returns: Product, Plant, ConsumptionRefUsageStartDate, "
            "ConsumptionQtyMultiplier, ConsumptionReferenceProduct."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "plant": {"type": "string", "description": "Plant code."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "plant"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductPlantIntlTrd
    # ------------------------------------------------------------------
    {
        "name": "list_product_plant_intl_trade",
        "description": (
            "Returns international trade / foreign trade data for products at plant level "
            "(entity: A_ProductPlantIntlTrd). "
            "Key fields: Product, Plant, CountryOfOrigin, RegionOfOrigin, "
            "ConsumptionTaxCtrlCode, ExportAndImportProductGroup, "
            "ProductCASNumber, UNDangerousGoodsNumber, ProdIntlTradeClassification."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_plant_intl_trade",
        "description": (
            "Returns international trade data for a specific product and plant "
            "(A_ProductPlantIntlTrd). "
            "Returns: Product, Plant, CountryOfOrigin, RegionOfOrigin, "
            "ConsumptionTaxCtrlCode, ExportAndImportProductGroup, "
            "ProductCASNumber, UNDangerousGoodsNumber."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "plant": {"type": "string", "description": "Plant code."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "plant"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductPlantMRPArea
    # ------------------------------------------------------------------
    {
        "name": "list_product_plant_mrp_areas",
        "description": (
            "Returns MRP area data for products at plant level (entity: A_ProductPlantMRPArea). "
            "Key fields: Product, Plant, MRPArea, MRPType (PD=MRP, VB=reorder point, etc.), "
            "MRPController, ReorderThresholdQuantity, PlanningTimeFence, "
            "MaximumStockQuantity, MinimumDeliveryQuantity, FixedLotSizeQuantity, "
            "LotSizingProcedure, SafetyStockQuantity, SafetyDuration, "
            "PlannedDeliveryDurationInDays, StorageLocation. "
            "Filter example: \"MRPType eq 'PD' and Plant eq '1010'\"."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_plant_mrp_area",
        "description": (
            "Returns MRP area data for a specific product, plant and MRP area "
            "(A_ProductPlantMRPArea). "
            "Returns: Product, Plant, MRPArea, MRPType, MRPController, "
            "ReorderThresholdQuantity, MaximumStockQuantity, SafetyStockQuantity, "
            "LotSizingProcedure, PlannedDeliveryDurationInDays."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "plant": {"type": "string", "description": "Plant code."},
                "mrp_area": {"type": "string", "description": "MRP area code."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "plant", "mrp_area"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductPlantProcurement
    # ------------------------------------------------------------------
    {
        "name": "list_product_plant_procurement",
        "description": (
            "Returns plant-level procurement data for products (entity: A_ProductPlantProcurement). "
            "Key fields: Product, Plant, IsAutoPurOrdCreationAllowed, "
            "IsSourceListRequired, JITDeliverySchedulesProfile."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_plant_procurement",
        "description": (
            "Returns plant-level procurement data for a specific product and plant "
            "(A_ProductPlantProcurement). "
            "Returns: Product, Plant, IsAutoPurOrdCreationAllowed, "
            "IsSourceListRequired, JITDeliverySchedulesProfile."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "plant": {"type": "string", "description": "Plant code."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "plant"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductPlantQualityMgmt
    # ------------------------------------------------------------------
    {
        "name": "list_product_plant_quality_mgmt",
        "description": (
            "Returns plant-level quality management data for products "
            "(entity: A_ProductPlantQualityMgmt). "
            "Key fields: Product, Plant, MaximumStoragePeriod, MaximumStoragePeriodUnit, "
            "QualityInspectionGroup, HasPostToInspectionStock, InspLotDocumentationIsRequired, "
            "SuplrQualityManagementSystem, RecrrgInspIntervalTimeInDays, "
            "ProductQualityCertificateType."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_plant_quality_mgmt",
        "description": (
            "Returns plant-level quality management data for a specific product and plant "
            "(A_ProductPlantQualityMgmt). "
            "Returns: Product, Plant, MaximumStoragePeriod, QualityInspectionGroup, "
            "HasPostToInspectionStock, InspLotDocumentationIsRequired."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "plant": {"type": "string", "description": "Plant code."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "plant"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductPlantSales
    # ------------------------------------------------------------------
    {
        "name": "list_product_plant_sales",
        "description": (
            "Returns plant-level sales data for products (entity: A_ProductPlantSales). "
            "Key fields: Product, Plant, LoadingGroup, AvailabilityCheckType, "
            "ReplacementPartType, CapitalGoodsAndServicesGroup."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_plant_sales",
        "description": (
            "Returns plant-level sales data for a specific product and plant "
            "(A_ProductPlantSales). "
            "Returns: Product, Plant, LoadingGroup, AvailabilityCheckType, "
            "ReplacementPartType, CapitalGoodsAndServicesGroup."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "plant": {"type": "string", "description": "Plant code."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "plant"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductPlantStorage
    # ------------------------------------------------------------------
    {
        "name": "list_product_plant_storage",
        "description": (
            "Returns plant-level warehouse/storage data for products "
            "(entity: A_ProductPlantStorage). "
            "Key fields: Product, Plant, PhysInventoryForCycleCountingInd, "
            "WrkCtrIssuingStorageLocation, WrkCtrReceivingStorageLocation."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_plant_storage",
        "description": (
            "Returns plant-level warehouse/storage data for a specific product and plant "
            "(A_ProductPlantStorage). "
            "Returns: Product, Plant, PhysInventoryForCycleCountingInd, "
            "WrkCtrIssuingStorageLocation, WrkCtrReceivingStorageLocation."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "plant": {"type": "string", "description": "Plant code."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "plant"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductPlantText
    # ------------------------------------------------------------------
    {
        "name": "list_product_plant_texts",
        "description": (
            "Returns plant-level long texts for products (entity: A_ProductPlantText). "
            "Key fields: Product, Plant, Language, LongText."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_plant_text",
        "description": (
            "Returns the plant-level long text for a specific product and plant "
            "(A_ProductPlantText). Returns: Product, Plant, Language, LongText."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "plant": {"type": "string", "description": "Plant code."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "plant"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductSalesDelivery
    # ------------------------------------------------------------------
    {
        "name": "list_product_sales_delivery",
        "description": (
            "Returns sales organization / distribution channel data for products "
            "(entity: A_ProductSalesDelivery). "
            "Key fields: Product, ProductSalesOrg, ProductDistributionChnl, "
            "ProductSalesStatus, ProductSalesStatusValidityDate, "
            "ItemCategoryGroup, SalesUnit, MinimumOrderQuantity, "
            "MinimumDeliveryQuantity, DeliveryQuantityUnit, "
            "AccountDetnProductGroup, PricingRefProduct, "
            "ProductHierarchy, IsMarkedForDeletion. "
            "Filter examples: \"ProductSalesOrg eq '1010'\", "
            "\"ProductDistributionChnl eq '10'\"."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_sales_delivery",
        "description": (
            "Returns sales organization data for a specific product, sales org and "
            "distribution channel (A_ProductSalesDelivery). "
            "Returns: Product, ProductSalesOrg, ProductDistributionChnl, "
            "ProductSalesStatus, ItemCategoryGroup, SalesUnit, "
            "MinimumOrderQuantity, AccountDetnProductGroup, PricingRefProduct."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "sales_org": {"type": "string", "description": "Sales organization code, e.g. '1010'."},
                "distribution_channel": {"type": "string", "description": "Distribution channel code, e.g. '10'."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "sales_org", "distribution_channel"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductSalesTax
    # ------------------------------------------------------------------
    {
        "name": "list_product_sales_tax",
        "description": (
            "Returns sales tax classification data for products (entity: A_ProductSalesTax). "
            "Key fields: Product, Country, TaxCategory, TaxClassification. "
            "Filter example: \"Country eq 'DE'\"."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_sales_tax",
        "description": (
            "Returns sales tax data for a specific product, country, tax category and "
            "tax classification (A_ProductSalesTax). "
            "Returns: Product, Country, TaxCategory, TaxClassification."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "country": {"type": "string", "description": "Country key, e.g. 'DE'."},
                "tax_category": {"type": "string", "description": "Tax category."},
                "tax_classification": {"type": "string", "description": "Tax classification."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "country", "tax_category", "tax_classification"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductSalesText
    # ------------------------------------------------------------------
    {
        "name": "list_product_sales_texts",
        "description": (
            "Returns sales long texts for products (entity: A_ProductSalesText). "
            "Key fields: Product, ProductSalesOrg, ProductDistributionChnl, Language, LongText."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_sales_text",
        "description": (
            "Returns the sales long text for a specific product, sales org, distribution channel "
            "and language (A_ProductSalesText). "
            "Returns: Product, ProductSalesOrg, ProductDistributionChnl, Language, LongText."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "sales_org": {"type": "string", "description": "Sales organization code."},
                "distribution_channel": {"type": "string", "description": "Distribution channel code."},
                "language": {"type": "string", "description": "Language key, e.g. 'EN'."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "sales_org", "distribution_channel", "language"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductStorageLocation
    # ------------------------------------------------------------------
    {
        "name": "list_product_storage_locations",
        "description": (
            "Returns storage location data for products (entity: A_ProductStorageLocation). "
            "Key fields: Product, Plant, StorageLocation, WarehouseStorageBin, "
            "IsMarkedForDeletion. "
            "Filter example: \"Plant eq '1010' and StorageLocation eq '0001'\"."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_storage_location",
        "description": (
            "Returns storage location data for a specific product, plant and storage location "
            "(A_ProductStorageLocation). "
            "Returns: Product, Plant, StorageLocation, WarehouseStorageBin, IsMarkedForDeletion."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "plant": {"type": "string", "description": "Plant code."},
                "storage_location": {"type": "string", "description": "Storage location code, e.g. '0001'."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "plant", "storage_location"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductSupplyPlanning
    # ------------------------------------------------------------------
    {
        "name": "list_product_supply_planning",
        "description": (
            "Returns supply planning (MRP) data for products at plant level "
            "(entity: A_ProductSupplyPlanning). "
            "Key fields: Product, Plant, MRPType, MRPController, "
            "ReorderThresholdQuantity, PlanningTimeFence, MaximumStockQuantity, "
            "MinimumDeliveryQuantity, FixedLotSizeQuantity, LotSizingProcedure, "
            "SafetyStockQuantity, SafetyDuration, PlannedDeliveryDurationInDays, "
            "GoodsReceiptDuration, ProductionInvtryManagedLoc. "
            "Filter example: \"MRPType eq 'PD' and Plant eq '1010'\"."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_supply_planning",
        "description": (
            "Returns supply planning (MRP) data for a specific product and plant "
            "(A_ProductSupplyPlanning). "
            "Returns: Product, Plant, MRPType, MRPController, ReorderThresholdQuantity, "
            "MaximumStockQuantity, SafetyStockQuantity, LotSizingProcedure, "
            "PlannedDeliveryDurationInDays, GoodsReceiptDuration."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "plant": {"type": "string", "description": "Plant code."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "plant"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductUnitsOfMeasure
    # ------------------------------------------------------------------
    {
        "name": "list_product_units_of_measure",
        "description": (
            "Returns units of measure (UoM) for products (entity: A_ProductUnitsOfMeasure). "
            "Key fields: Product, AlternativeUnit, QuantityNumerator, QuantityDenominator, "
            "Length, Width, Height, DimensionUnit, Volume, VolumeUnit, "
            "GrossWeight, WeightUnit, LowerLevelPackagingUnit, MaximumStackingFactor. "
            "Filter example: \"AlternativeUnit eq 'KG'\"."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_unit_of_measure",
        "description": (
            "Returns a specific unit of measure for a product (A_ProductUnitsOfMeasure). "
            "Returns: Product, AlternativeUnit, QuantityNumerator, QuantityDenominator, "
            "Length, Width, Height, DimensionUnit, Volume, VolumeUnit, GrossWeight, WeightUnit."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "alternative_unit": {"type": "string", "description": "Alternative unit of measure, e.g. 'KG', 'EA'."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "alternative_unit"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductUnitsOfMeasureEAN (GTIN)
    # ------------------------------------------------------------------
    {
        "name": "list_product_ean_codes",
        "description": (
            "Returns GTIN/EAN barcode data for products (entity: A_ProductUnitsOfMeasureEAN). "
            "Key fields: Product, AlternativeUnit, ConsecutiveNumber, "
            "ProductStandardID (the EAN/GTIN value), InternationalArticleNumberCat (EAN type). "
            "Filter example: \"ProductStandardID eq '4012345678901'\"."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_ean_code",
        "description": (
            "Returns a specific GTIN/EAN code for a product, alternative unit and consecutive "
            "number (A_ProductUnitsOfMeasureEAN). "
            "Returns: Product, AlternativeUnit, ConsecutiveNumber, "
            "ProductStandardID, InternationalArticleNumberCat."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "alternative_unit": {"type": "string", "description": "Alternative unit of measure."},
                "consecutive_number": {"type": "string", "description": "Consecutive number."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "alternative_unit", "consecutive_number"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductValuation
    # ------------------------------------------------------------------
    {
        "name": "list_product_valuations",
        "description": (
            "Returns valuation area data for products (entity: A_ProductValuation). "
            "Key fields: Product, ValuationArea, ValuationType, "
            "StandardPrice, MovingAveragePrice, PriceUnitQty, PriceLastChangeDate, "
            "ValuationClass, PriceDeterminationControl, "
            "InventoryValuationProcedure, IsMarkedForDeletion. "
            "Filter examples: \"ValuationArea eq '1010'\", \"ValuationType eq ''\"."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_valuation",
        "description": (
            "Returns valuation data for a specific product, valuation area and valuation type "
            "(A_ProductValuation). "
            "Returns: Product, ValuationArea, ValuationType, StandardPrice, "
            "MovingAveragePrice, PriceUnitQty, PriceLastChangeDate, ValuationClass, "
            "InventoryValuationProcedure."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "valuation_area": {"type": "string", "description": "Valuation area, e.g. '1010'."},
                "valuation_type": {"type": "string", "description": "Valuation type (use empty string '' if not split-valuated)."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "valuation_area", "valuation_type"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductValuationAccount
    # ------------------------------------------------------------------
    {
        "name": "list_product_valuation_accounts",
        "description": (
            "Returns valuation account assignment data for products "
            "(entity: A_ProductValuationAccount). "
            "Key fields: Product, ValuationArea, ValuationType, "
            "CommercialPrice1, CommercialPrice2, CommercialPrice3, "
            "TaxBasedPrices1, TaxBasedPrices2, TaxBasedPrices3."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_valuation_account",
        "description": (
            "Returns valuation account data for a specific product, valuation area and "
            "valuation type (A_ProductValuationAccount). "
            "Returns: Product, ValuationArea, ValuationType, "
            "CommercialPrice1, CommercialPrice2, CommercialPrice3, "
            "TaxBasedPrices1, TaxBasedPrices2, TaxBasedPrices3."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "valuation_area": {"type": "string", "description": "Valuation area."},
                "valuation_type": {"type": "string", "description": "Valuation type."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "valuation_area", "valuation_type"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductValuationCosting
    # ------------------------------------------------------------------
    {
        "name": "list_product_valuation_costing",
        "description": (
            "Returns valuation costing data for products (entity: A_ProductValuationCosting). "
            "Key fields: Product, ValuationArea, ValuationType, "
            "CostEstimateNumber, ProductCostEstimateStatus, "
            "CostEstimateValidityStartDate, CostEstimateValidityEndDate."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_valuation_costing",
        "description": (
            "Returns valuation costing data for a specific product, valuation area and "
            "valuation type (A_ProductValuationCosting). "
            "Returns: Product, ValuationArea, ValuationType, CostEstimateNumber, "
            "ProductCostEstimateStatus, CostEstimateValidityStartDate, "
            "CostEstimateValidityEndDate."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "valuation_area": {"type": "string", "description": "Valuation area."},
                "valuation_type": {"type": "string", "description": "Valuation type."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "valuation_area", "valuation_type"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductMLAccount
    # ------------------------------------------------------------------
    {
        "name": "list_product_ml_accounts",
        "description": (
            "Returns material ledger account data for products (entity: A_ProductMLAccount). "
            "Key fields: Product, ValuationArea, ValuationType, CurrencyRole, "
            "Currency, InventoryAmount, CumulatedInventoryAmount."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_ml_account",
        "description": (
            "Returns material ledger account data for a specific product, valuation area, "
            "valuation type and currency role (A_ProductMLAccount). "
            "Returns: Product, ValuationArea, ValuationType, CurrencyRole, "
            "Currency, InventoryAmount, CumulatedInventoryAmount."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "valuation_area": {"type": "string", "description": "Valuation area."},
                "valuation_type": {"type": "string", "description": "Valuation type."},
                "currency_role": {"type": "string", "description": "Currency role (e.g. '10'=company code currency)."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "valuation_area", "valuation_type", "currency_role"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductMLPrices
    # ------------------------------------------------------------------
    {
        "name": "list_product_ml_prices",
        "description": (
            "Returns material ledger price data for products (entity: A_ProductMLPrices). "
            "Key fields: Product, ValuationArea, ValuationType, CurrencyRole, "
            "Currency, InventoryUnitCost, MovingAveragePrice, StandardPrice."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_ml_price",
        "description": (
            "Returns material ledger price data for a specific product, valuation area, "
            "valuation type and currency role (A_ProductMLPrices). "
            "Returns: Product, ValuationArea, ValuationType, CurrencyRole, "
            "Currency, InventoryUnitCost, MovingAveragePrice, StandardPrice."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "valuation_area": {"type": "string", "description": "Valuation area."},
                "valuation_type": {"type": "string", "description": "Valuation type."},
                "currency_role": {"type": "string", "description": "Currency role."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "valuation_area", "valuation_type", "currency_role"],
        },
    },
    # ------------------------------------------------------------------
    # A_ProductWorkScheduling
    # ------------------------------------------------------------------
    {
        "name": "list_product_work_scheduling",
        "description": (
            "Returns work scheduling data for products at plant level "
            "(entity: A_ProductWorkScheduling). "
            "Key fields: Product, Plant, ProductionUnit, ProductionInvtryManagedLoc, "
            "ProductProcessingTime, ProductionSupervisor, ProductionSchedulingProfile, "
            "SetupAndTeardownTime, TransitionMatrixProductsGroup, UnderdlvTolerance."
        ),
        "inputSchema": {"type": "object", "properties": _LIST_PARAMS},
    },
    {
        "name": "get_product_work_scheduling",
        "description": (
            "Returns work scheduling data for a specific product and plant "
            "(A_ProductWorkScheduling). "
            "Returns: Product, Plant, ProductionUnit, ProductProcessingTime, "
            "ProductionSupervisor, ProductionSchedulingProfile, "
            "SetupAndTeardownTime, UnderdlvTolerance."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string", "description": "Product number."},
                "plant": {"type": "string", "description": "Plant code."},
                **_SINGLE_PARAMS,
            },
            "required": ["product", "plant"],
        },
    },
]

TOOLS_BY_NAME = {t["name"]: t for t in TOOLS}
