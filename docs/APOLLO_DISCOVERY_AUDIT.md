# Apollo Discovery Audit

This audit covers the Apollo integration used by the discovery provider. The refactor keeps the existing CRM, qualification, contact-import, API, database, and frontend contracts unchanged.

## Organization Search

- Endpoint: `POST /mixed_companies/search`
- Purpose: Find organizations for one focused Industry Pack strategy.
- Request body: none. Apollo filters are sent as query parameters.
- Request parameters: `page`, `per_page`, `organization_locations[]`, `organization_num_employees_ranges[]`, `q_organization_keyword_tags[]`, `q_keywords`, `excluded_organization_keyword_tags[]`, and configured `organization_*` provider filters.
- Strategy rule: one exact/related industry and one product keyword per request. Broad industries and process/manufacturing terms are not used as Apollo organization-search keywords.
- Response collections accepted: `organizations`, `companies`, `accounts`, or `results`.

### Organization Mapping

The mapper now prefers known paths and recursively searches the complete organization record when those paths are absent:

| Normalized field | Preferred paths |
| --- | --- |
| Company name | `name`, `organization_name`, `company_name`, nested organization/account name |
| Country | organization/location/address country fields |
| Region | organization/location region/state fields |
| City | organization/location/address city fields |
| Industry | `industry`, `primary_industry`, organization industry fields, `industries` |
| Employee count | estimated, organization, employee count variants |
| Description | description, short description, headline, summary variants |
| Website | primary domain, domain, website variants |
| LinkedIn | LinkedIn URL variants |
| Revenue | annual, estimated annual, and revenue variants |
| Technologies | technologies and technology-name variants |

Each mapping entry records the selected JSON path, alternate paths, extracted value, whether recursive fallback was used, confidence (`high`, `medium`, or `missing`), and why a value is unknown when Apollo did not return one.

The record also stores `unused_apollo_fields`, a list of raw leaf paths not consumed by the normalized mapping for that response.

## People Search

- Endpoint: `POST /mixed_people/api_search`
- Purpose: Search contacts for a discovered organization.
- Request parameters: page, page size, organization domain/ID, organization location and employee filters, Apollo seniority filters, one title tier, and the focused product keyword.
- Response collections accepted: `people`, `contacts`, or `results`.
- Contact fields mapped: ID, name, title, email, phone, LinkedIn, seniority, email status, country, and region.
- People Search runs after the organization passes Discovery Confidence. If it is not run, the staging record is explicitly marked `discovery_confidence` / `low_discovery_confidence`; it is not silently omitted.

## Raw and Diagnostic Data

With `DISCOVERY_DIAGNOSTIC_MODE=true`, each staging record retains the complete Apollo response, request parameters, normalized company/contact data, and mapping report. Organization responses are also written to `backend/data/raw_apollo/run_<run_id>/organization_<apollo_id>.json` without truncation.

Apollo fields that are not part of the existing CRM model, such as revenue, technologies, and organization LinkedIn, remain available in the normalized diagnostic JSON and raw payload metadata without a schema migration.

## Known Assumptions

- Apollo returns organization and people results in one of the supported collection keys above.
- Apollo API filters are accepted as query parameters by the configured endpoint.
- No website scraping is performed.
- Apollo retries are handled inside the provider; the discovery quota counts one logical provider search before it is attempted.
