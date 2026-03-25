# SAP Product Master MCP Server

A **Flask-based MCP (Model Context Protocol) server** that exposes SAP S/4HANA
`API_PRODUCT_SRV` GET endpoints as MCP tools, enabling AI assistants like
**SAP Joule** to query product master data via natural language.

## Agent Description

> Copy this text into your AI agent's system prompt or MCP server registration
> to help Joule understand what this server provides and when to use it.

This MCP server provides read-only access to SAP S/4HANA product master data
via the `API_PRODUCT_SRV` OData v2 service. It exposes tools to query all
aspects of a product's master record, including basic product attributes,
descriptions (by language), plant-level data (MRP, costing, procurement,
storage, quality management, work scheduling, forecasting), sales organization
data, valuation and material ledger data, units of measure with GTIN/EAN codes,
and storage locations. Each entity type has a `list_*` tool (supporting
`$filter`, `$select`, `$top`, `$skip`, `$orderby`, `$expand`) and a `get_*`
tool for direct key-based lookup. All tools return JSON-formatted OData
responses from the connected S/4HANA system. Use these tools to answer
questions about product existence, classification, descriptions, plant
assignments, pricing, units of measure, and procurement or sales configuration.

---

## Architecture

```
Joule / MCP Client
      |
      |  MCP tool call
      v
Flask MCP Server  (this service)
      |
      |  Destination lookup
      v
SAP BTP Destination Service
      |
      |  HTTP GET
      v
S/4HANA API_PRODUCT_SRV
```

### MCP Transport

| Endpoint | Method | Transport | Client |
|---|---|---|---|
| `/mcp` | POST | Streamable HTTP (MCP 2025-03-26) | **SAP Joule Studio** |
| `/mcp` | GET | — | Discovery / health check |
| `/sse` | GET | HTTP + SSE (legacy) | Claude Desktop, generic SSE clients |
| `/messages?sessionId=<id>` | POST | HTTP + SSE (legacy) | Paired with `/sse` |
| `/health` | GET | — | Liveness probe |

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.prod .env
# Edit .env with your SAP BTP credentials
```

### 3. Run the server

```bash
python3 app.py
```

The server starts on `http://0.0.0.0:5001` by default.

---

## Configuration

The server resolves credentials in this order:

| Priority | Source | When to use |
|---|---|---|
| 1 | **`VCAP_SERVICES`** (auto-injected by CF) | App is deployed on CF with Destination service **bound** |
| 2 | **`DESTINATION_SERVICE_*` env vars** | Local dev, CI, or manual override |
| 3 | **`S4_BASE_URL` / `S4_*` env vars** | Local dev without BTP |

### Option A – CF deployment with bound Destination service (recommended)

When the Destination service instance is **bound** to the CF app (via `manifest.yml`
or `cf bind-service`), CF automatically injects its credentials into `VCAP_SERVICES`.
The app reads them at startup — **no manual credential env vars needed**.

The only variable you must set is:

| Variable | Description |
|---|---|
| `DESTINATION_NAME` | Name of the destination entry in BTP Cockpit → Connectivity → Destinations |

### Option B – Manual env vars (local dev / CI)

Use this when running outside CF or when you want to override the bound service.
Set the following variables in `.env`:

| Variable | Description |
|---|---|
| `DESTINATION_SERVICE_AUTH_URL` | XSUAA token URL, e.g. `https://<subdomain>.authentication.<region>.hana.ondemand.com/oauth/token` |
| `DESTINATION_SERVICE_CLIENT_ID` | OAuth2 client ID from the service binding |
| `DESTINATION_SERVICE_CLIENT_SECRET` | OAuth2 client secret |
| `DESTINATION_SERVICE_URL` | Destination service REST API base URL |
| `DESTINATION_NAME` | Name of the destination in BTP Cockpit |

The destination in BTP Cockpit should point to your S/4HANA system and be
configured with the appropriate authentication (BasicAuthentication or OAuth2).

### Option C – Direct S/4HANA connection (local dev / testing)

Set these variables instead of the Destination service ones:

| Variable | Description |
|---|---|
| `S4_BASE_URL` | Direct S/4HANA base URL, e.g. `https://my-s4.example.com` |
| `S4_USERNAME` | Basic auth username |
| `S4_PASSWORD` | Basic auth password |

---

## Available MCP Tools

The server exposes **46 tools** covering all GET endpoints of `API_PRODUCT_SRV`:

| Tool | OData Endpoint | Description |
|---|---|---|
| `list_products` | `GET /A_Product` | List product master records |
| `get_product` | `GET /A_Product('{Product}')` | Get product by number |
| `list_product_descriptions` | `GET /A_ProductDescription` | List product descriptions |
| `get_product_description` | `GET /A_ProductDescription(Product,Language)` | Get description by product + language |
| `list_product_basic_texts` | `GET /A_ProductBasicText` | List basic data texts |
| `get_product_basic_text` | `GET /A_ProductBasicText(Product,Language)` | Get basic text by product + language |
| `list_product_inspection_texts` | `GET /A_ProductInspectionText` | List inspection texts |
| `get_product_inspection_text` | `GET /A_ProductInspectionText(Product,Language)` | Get inspection text |
| `list_product_procurement` | `GET /A_ProductProcurement` | List procurement data |
| `get_product_procurement` | `GET /A_ProductProcurement('{Product}')` | Get procurement data by product |
| `list_product_purchase_texts` | `GET /A_ProductPurchaseText` | List purchase texts |
| `get_product_purchase_text` | `GET /A_ProductPurchaseText(Product,Language)` | Get purchase text |
| `list_product_quality_mgmt` | `GET /A_ProductQualityMgmt` | List quality management data |
| `get_product_quality_mgmt` | `GET /A_ProductQualityMgmt('{Product}')` | Get quality mgmt data |
| `list_product_sales` | `GET /A_ProductSales` | List basic sales data |
| `get_product_sales` | `GET /A_ProductSales('{Product}')` | Get sales data by product |
| `list_product_storage` | `GET /A_ProductStorage` | List basic storage data |
| `get_product_storage` | `GET /A_ProductStorage('{Product}')` | Get storage data by product |
| `list_product_plants` | `GET /A_ProductPlant` | List plant data |
| `get_product_plant` | `GET /A_ProductPlant(Product,Plant)` | Get plant data |
| `list_product_plant_costing` | `GET /A_ProductPlantCosting` | List plant costing data |
| `get_product_plant_costing` | `GET /A_ProductPlantCosting(Product,Plant)` | Get plant costing data |
| `list_product_plant_forecasting` | `GET /A_ProductPlantForecasting` | List forecasting data |
| `get_product_plant_forecasting` | `GET /A_ProductPlantForecasting(Product,Plant)` | Get forecasting data |
| `list_product_plant_intl_trade` | `GET /A_ProductPlantIntlTrd` | List international trade data |
| `get_product_plant_intl_trade` | `GET /A_ProductPlantIntlTrd(Product,Plant)` | Get international trade data |
| `list_product_plant_mrp_areas` | `GET /A_ProductPlantMRPArea` | List MRP area data |
| `get_product_plant_mrp_area` | `GET /A_ProductPlantMRPArea(Product,Plant,MRPArea)` | Get MRP area data |
| `list_product_plant_procurement` | `GET /A_ProductPlantProcurement` | List plant procurement data |
| `get_product_plant_procurement` | `GET /A_ProductPlantProcurement(Product,Plant)` | Get plant procurement data |
| `list_product_plant_quality_mgmt` | `GET /A_ProductPlantQualityMgmt` | List plant quality mgmt data |
| `get_product_plant_quality_mgmt` | `GET /A_ProductPlantQualityMgmt(Product,Plant)` | Get plant quality mgmt data |
| `list_product_plant_sales` | `GET /A_ProductPlantSales` | List plant sales data |
| `get_product_plant_sales` | `GET /A_ProductPlantSales(Product,Plant)` | Get plant sales data |
| `list_product_plant_storage` | `GET /A_ProductPlantStorage` | List plant storage data |
| `get_product_plant_storage` | `GET /A_ProductPlantStorage(Product,Plant)` | Get plant storage data |
| `list_product_plant_texts` | `GET /A_ProductPlantText` | List plant texts |
| `get_product_plant_text` | `GET /A_ProductPlantText(Product,Plant)` | Get plant text |
| `list_product_sales_delivery` | `GET /A_ProductSalesDelivery` | List sales org data |
| `get_product_sales_delivery` | `GET /A_ProductSalesDelivery(Product,SalesOrg,DistrChnl)` | Get sales org data |
| `list_product_sales_tax` | `GET /A_ProductSalesTax` | List sales tax data |
| `get_product_sales_tax` | `GET /A_ProductSalesTax(Product,Country,TaxCat,TaxCls)` | Get sales tax data |
| `list_product_sales_texts` | `GET /A_ProductSalesText` | List sales texts |
| `get_product_sales_text` | `GET /A_ProductSalesText(Product,SalesOrg,DistrChnl,Lang)` | Get sales text |
| `list_product_storage_locations` | `GET /A_ProductStorageLocation` | List storage locations |
| `get_product_storage_location` | `GET /A_ProductStorageLocation(Product,Plant,SLoc)` | Get storage location |
| `list_product_supply_planning` | `GET /A_ProductSupplyPlanning` | List supply planning data |
| `get_product_supply_planning` | `GET /A_ProductSupplyPlanning(Product,Plant)` | Get supply planning data |
| `list_product_units_of_measure` | `GET /A_ProductUnitsOfMeasure` | List units of measure |
| `get_product_unit_of_measure` | `GET /A_ProductUnitsOfMeasure(Product,AltUnit)` | Get unit of measure |
| `list_product_ean_codes` | `GET /A_ProductUnitsOfMeasureEAN` | List GTIN/EAN codes |
| `get_product_ean_code` | `GET /A_ProductUnitsOfMeasureEAN(Product,AltUnit,Consec)` | Get GTIN/EAN code |
| `list_product_valuations` | `GET /A_ProductValuation` | List valuation data |
| `get_product_valuation` | `GET /A_ProductValuation(Product,ValArea,ValType)` | Get valuation data |
| `list_product_valuation_accounts` | `GET /A_ProductValuationAccount` | List valuation accounts |
| `get_product_valuation_account` | `GET /A_ProductValuationAccount(Product,ValArea,ValType)` | Get valuation account |
| `list_product_valuation_costing` | `GET /A_ProductValuationCosting` | List valuation costing |
| `get_product_valuation_costing` | `GET /A_ProductValuationCosting(Product,ValArea,ValType)` | Get valuation costing |
| `list_product_ml_accounts` | `GET /A_ProductMLAccount` | List material ledger accounts |
| `get_product_ml_account` | `GET /A_ProductMLAccount(Product,ValArea,ValType,CurrRole)` | Get ML account |
| `list_product_ml_prices` | `GET /A_ProductMLPrices` | List material ledger prices |
| `get_product_ml_price` | `GET /A_ProductMLPrices(Product,ValArea,ValType,CurrRole)` | Get ML price |
| `list_product_work_scheduling` | `GET /A_ProductWorkScheduling` | List work scheduling data |
| `get_product_work_scheduling` | `GET /A_ProductWorkScheduling(Product,Plant)` | Get work scheduling data |

### Common OData Parameters (list tools)

All `list_*` tools accept these optional parameters:

| Parameter | OData | Example |
|---|---|---|
| `top` | `$top` | `10` |
| `skip` | `$skip` | `20` |
| `filter` | `$filter` | `"ProductType eq 'FERT'"` |
| `select` | `$select` | `"Product,ProductType,BaseUnit"` |
| `orderby` | `$orderby` | `"Product asc"` |
| `expand` | `$expand` | `"to_Description,to_Plant"` |

---

## Project Structure

```
mcp_server/
├── app.py                  # Flask MCP server (SSE transport, JSON-RPC handler)
├── tools.py                # MCP tool definitions (inputSchema for all 62 tools)
├── tool_executor.py        # Dispatches tool calls to OData endpoints
├── sap_destination.py      # SAP BTP Destination Service client
├── requirements.txt        # Python dependencies
├── manifest.yml            # Cloud Foundry deployment manifest (cf push)
├── .env.example            # Environment variable template
├── .env.local              # Local dev overrides (Option B – direct S/4HANA)
├── .env.prod               # BTP/prod overrides  (Option A – Destination Service)
└── README.md               # This file
```

---

## SAP BTP Setup

### 1. Create a Destination in BTP Cockpit

1. Go to **BTP Cockpit** → your subaccount → **Connectivity** → **Destinations**
2. Create a new destination:
   - **Name**: `S4HANA_PRODUCT_SRV` (must match `DESTINATION_NAME` in `.env`)
   - **Type**: HTTP
   - **URL**: `https://<your-s4hana-host>`
   - **Authentication**: `BasicAuthentication` (or `OAuth2ClientCredentials`)
   - **User** / **Password**: your S/4HANA API user credentials

### 2. Create Service Instances

**Destination service** (required for all deployment modes):
1. Go to **BTP Cockpit** → **Instances and Subscriptions**
2. Create a **Destination** service instance (plan: `lite`)

**Connectivity service** (required for PrincipalPropagation / on-premise S/4HANA via Cloud Connector):
1. In the same screen, create a **Connectivity** service instance (plan: `lite`)

Both instances will be bound to the CF app via `manifest.yml` — no manual credential setup needed.

### 3. Ensure API_PRODUCT_SRV is accessible

The S/4HANA user must have authorization for:
- OData service: `API_PRODUCT_SRV`
- Authorization object: `M_MATE_MAR` (Material Master)

---

## Deploy to SAP BTP Cloud Foundry

This section walks through deploying the MCP server as a Cloud Foundry application
in your SAP BTP subaccount.

### Prerequisites

- [CF CLI v8+](https://docs.cloudfoundry.org/cf-cli/install-go-cli.html) installed
- A BTP subaccount with **Cloud Foundry environment** enabled
- A **Destination service instance** (plan: `lite`) already created (see [SAP BTP Setup](#sap-btp-setup) above)
- A **Destination** entry configured in BTP Cockpit pointing to your S/4HANA system

### 1. Log in to Cloud Foundry

```bash
cf login -a https://api.cf.<region>.hana.ondemand.com --sso
# e.g. https://api.cf.eu10.hana.ondemand.com
```

Select your org and space when prompted.

### 2. Review `manifest.yml`

A `manifest.yml` is included in the project root. Open it and update:

- **`services`** – replace `destination-service-instance` with the actual name of
  your Destination service instance in BTP Cockpit
- **`DESTINATION_NAME`** – must match the destination entry name in
  BTP Cockpit → Connectivity → Destinations

```yaml
services:
  - my-destination-service      # ← your Destination service instance name
  - my-connectivity-service     # ← your Connectivity service instance name (required for PrincipalPropagation)

env:
  DESTINATION_NAME: S4HANA_PRODUCT_SRV   # ← your destination entry name
```

> **Note:** The Connectivity service is required when the BTP destination uses
> **PrincipalPropagation** authentication (on-premise S/4HANA via Cloud Connector).
> If your destination uses BasicAuthentication or OAuth2, you can omit it.

### 3. Push the app without starting it

```bash
cf push --no-start
```

This uploads the files and creates the app in CF (so `cf set-env` can target it),
but does **not** start it yet — avoiding a failed start due to missing credentials.

### 4. Set the destination name

The only env var you need to set manually is the name of the destination entry
in BTP Cockpit. The Destination service credentials are read automatically from
`VCAP_SERVICES` once the service is bound (step 2 of the manifest).

```bash
cf set-env sap-product-mcp-server DESTINATION_NAME S4HANA_PRODUCT_SRV
```

Replace `S4HANA_PRODUCT_SRV` with the actual destination name you configured in
BTP Cockpit → Connectivity → Destinations.

### 5. Start the app

```bash
cf start sap-product-mcp-server
```

CF will:
1. Install Python dependencies from `requirements.txt` via the Python buildpack
2. Bind the Destination service instance
3. Inject all env vars (from `manifest.yml` + `cf set-env`)
4. Start the app with `python app.py` on port 8080

> **Redeploying after code changes:** run `cf push` — env vars set via `cf set-env`
> are stored in CF and **survive every push**. You do not need to repeat `cf set-env`.

### 6. Verify the deployment

Because `random-route: true` is set in `manifest.yml`, CF assigns a unique URL
(e.g. `sap-product-mcp-server-<adjective-noun>.<cf-apps-domain>`). Look it up with:

```bash
# Check app status — the assigned URL is shown in the "routes" line
cf app sap-product-mcp-server

# Tail recent logs
cf logs sap-product-mcp-server --recent

# Test the health endpoint (replace <random-route> with the actual route shown above)
curl https://<random-route>.<cf-apps-domain>/health
```

> **Note:** `cf set-env`, `cf start`, `cf logs`, and `cf restage` all use the
> **app name** (`sap-product-mcp-server`), not the route — so `random-route: true`
> has no effect on any of those commands.

Expected response:
```json
{"server": "sap-product-mcp-server", "status": "ok", "tools": 62, "version": "1.0.0"}
```

### 7. Register the CF URL with your MCP client

```json
{
  "mcpServers": {
    "sap-product-master": {
      "url": "https://sap-product-mcp-server.<cf-apps-domain>/sse",
      "transport": "sse"
    }
  }
}
```

### Switching between local dev and BTP

| Environment | Command | Connection mode |
|---|---|---|
| Local dev | `cp .env.local .env` | Option B – direct S/4HANA (`S4_*` vars) |
| Local test of prod config | `cp .env.prod .env` | Option A – Destination Service (`DESTINATION_*` vars) |
| BTP / CF deployment | `cf push` (uses `manifest.yml` + `cf set-env`) | Option A – Destination Service |

The server selects the mode automatically:
- `VCAP_SERVICES` present **and** `DESTINATION_NAME` set → **Option A** (bound CF service, credentials from VCAP)
- `DESTINATION_SERVICE_*` env vars present → **Option B** (manual env vars)
- Neither of the above → **Option C** (direct `S4_BASE_URL`)

---

## Registering with Joule / MCP Client

### Fields explained

| Field | Value | Notes |
|---|---|---|
| **URL / Path** | `https://<your-cf-route>/sse` | Full SSE endpoint URL. For local dev: `http://localhost:5001/sse`. The path is always `/sse`. |
| **Server name** | `sap-product-mcp-server` | The name the server reports in the MCP `initialize` handshake. Some clients display this; others let you override it. |

### Generic MCP client config

```json
{
  "mcpServers": {
    "sap-product-master": {
      "url": "https://<your-cf-route>/sse",
      "transport": "sse"
    }
  }
}
```

For local development replace the URL with `http://localhost:5001/sse`.

### SAP Joule Studio registration

Joule Studio uses **Streamable HTTP** transport and POSTs to `/mcp` by default.

- **URL**: `https://<your-cf-route>`  (base URL only — no path)
- **Path**: `/mcp`  (Joule Studio's default — leave as-is)
- **Namespace**: `sap_product` (or any short unique identifier you prefer)

> The previous `/sse` path caused a `405 Method Not Allowed` error because
> Joule Studio POSTs to the path, and `/sse` only accepts GET.
> The new `/mcp` endpoint accepts both GET and POST and returns JSON-RPC
> responses synchronously, which is what Joule Studio expects.

---

## Development

### Run locally with direct S/4HANA connection

```bash
cp .env.prod .env

python3 app.py
```

### Test the health endpoint

```bash
curl http://localhost:5001/health
```

### Test with Streamable HTTP (`/mcp`) — works locally and on CF

`/mcp` is a plain HTTP POST — no SSE session setup needed, making it the
easiest transport to test manually:

```bash
# List available tools
curl -s -X POST http://localhost:5001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | jq .

# Call a tool
curl -s -X POST http://localhost:5001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list_products","arguments":{"top":3}}}' | jq .
```

For Joule Studio local testing, set the URL to `http://localhost:5001` and path to `/mcp`.

### Test with SSE transport (`/sse`) — legacy clients

```bash
# 1. Open SSE stream (in one terminal)
curl -N http://localhost:5001/sse

# 2. Note the sessionId from the endpoint event, then POST a message
curl -X POST "http://localhost:5001/messages?sessionId=<sid>" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

# 3. Call a tool
curl -X POST "http://localhost:5001/messages?sessionId=<sid>" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "list_products",
      "arguments": {"top": 5, "filter": "ProductType eq '"'"'FERT'"'"'"}
    }
  }'
```
