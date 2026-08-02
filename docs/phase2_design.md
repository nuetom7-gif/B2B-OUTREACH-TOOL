# Phase 2 Sales Intelligence Platform Design

## Purpose

This document defines the Phase 2 architecture for the Yash Technology Outreach Hub.
It keeps the existing Phase 1 CRM intact and layers a discovery and qualification system on top of it.

The design goal is to move from manual lead entry toward a configurable sales intelligence platform that:

- discovers potential customer companies
- finds decision makers inside those companies
- qualifies and scores leads
- deduplicates against existing CRM data
- imports only qualified records
- preserves a manual-review path when Apollo data is not sufficient

Apollo is the only provider today, but the discovery engine must not be coupled to Apollo-specific logic.

---

## 1. Overall Architecture

```text
Scheduler
  -> Discovery Engine
    -> ICP Engine
      -> Provider Interface
        -> Apollo Provider
          -> Organization Search
          -> People Search
    -> Qualification Engine
    -> Duplicate Detection and Merge
    -> CRM Import
    -> Audit
```

### Design Principles

- The scheduler decides when to run.
- The discovery engine orchestrates the workflow.
- The ICP engine loads and interprets product-line configuration.
- The provider interface hides provider-specific API details.
- Apollo is the first and only provider implementation.
- Qualification happens before CRM import.
- Raw results are not imported blindly.
- Manual review is used when confidence is low.
- Existing Phase 1 logic remains the system of record for CRM behavior.

---

## 2. Discovery Lifecycle

The discovery lifecycle should be:

1. Load enabled ICP definitions from YAML.
2. Determine which product lines are due to run based on `search_frequency`.
3. For each due ICP:
   - request organizations from the provider
   - request people for each organization
   - normalize raw provider output into internal discovery results
4. Run qualification checks on the raw results.
5. Run duplicate detection and merge rules.
6. Import only qualified records into the CRM.
7. Mark uncertain items as `needs_manual_review`.
8. Write a run record with metrics and errors.
9. Emit audit events for all material changes.

The discovery engine must stop at manual review when the data is incomplete or ambiguous.
It must not scrape or enrich from any source outside the provider.

---

## 3. ICP YAML Schema

The ICP configuration should live in a dedicated YAML file.
It should be editable without code changes.
The schema should support future providers and future product lines.

### Proposed File

`backend/app/config/icp.yml`

### Example Schema

```yaml
product_lines:
  - product_name: "Industrial Vacuum Cleaning Systems"
    enabled: true
    country: ["India"]
    regions: ["West India", "North India"]
    target_industries:
      - "Laser Equipment Manufacturers"
      - "Electronics Manufacturing Services"
      - "PCB Manufacturers"
      - "Automotive Manufacturers"
      - "Metal Fabrication Companies"
    exclude_industries:
      - "Vacuum Equipment Suppliers"
      - "Dust Collector Manufacturers"
      - "Fume Extraction Manufacturers"
    company_keywords:
      - "manufacturing"
      - "fabrication"
      - "laser"
      - "electronics"
      - "pcb"
      - "automotive"
      - "pharma"
      - "medical device"
      - "textile"
      - "aerospace"
      - "food processing"
    exclude_keywords:
      - "supplier"
      - "distributor"
      - "dealer"
    apollo_filters:
      seniority: ["manager", "director", "vp", "head", "owner"]
      department: ["operations", "procurement", "maintenance", "safety", "engineering"]
      company_status: ["active"]
    employee_min: 20
    employee_max: 5000
    company_size: ["small", "medium", "large"]
    preferred_company_types:
      - "manufacturing"
      - "industrial"
    target_titles:
      - "Plant Head"
      - "Production Head"
      - "Factory Manager"
      - "Maintenance Manager"
      - "EHS Manager"
      - "Safety Manager"
      - "Purchase Manager"
      - "Procurement Manager"
      - "Operations Manager"
    preferred_titles:
      - "Plant Head"
      - "Factory Manager"
      - "Procurement Manager"
    decision_level:
      - "decision maker"
      - "influencer"
    lead_score_rules:
      industry_match: 30
      keyword_match: 20
      company_size_fit: 10
      decision_maker_found: 25
      verified_contact_present: 15
    search_frequency: "Daily"
    priority: 1

  - product_name: "Warehouse & Storage Solutions"
    enabled: true
    country: ["India"]
    regions: ["Pan India"]
    target_industries:
      - "3PL Logistics Companies"
      - "Warehousing Companies"
      - "Cold Storage Companies"
      - "E-commerce Fulfillment Centers"
      - "Automotive Warehouses"
      - "Pharmaceutical Distribution Companies"
      - "FMCG Distribution Companies"
      - "Retail Distribution Centers"
      - "Manufacturing Plants"
      - "Industrial Warehouses"
    exclude_industries:
      - "Warehouse Equipment Suppliers"
      - "Racking Manufacturers"
    company_keywords:
      - "logistics"
      - "warehousing"
      - "fulfillment"
      - "cold storage"
      - "distribution"
      - "warehouse"
      - "supply chain"
    exclude_keywords:
      - "supplier"
      - "manufacturer"
    apollo_filters:
      seniority: ["manager", "director", "vp", "head", "owner"]
      department: ["operations", "supply chain", "procurement", "projects"]
      company_status: ["active"]
    employee_min: 25
    employee_max: 10000
    company_size: ["small", "medium", "large"]
    preferred_company_types:
      - "logistics"
      - "warehouse"
      - "distribution"
    target_titles:
      - "Warehouse Manager"
      - "Supply Chain Manager"
      - "Procurement Manager"
      - "Purchase Manager"
      - "Projects Manager"
      - "Operations Manager"
      - "Factory Manager"
      - "Plant Head"
    preferred_titles:
      - "Warehouse Manager"
      - "Supply Chain Manager"
      - "Operations Manager"
    decision_level:
      - "decision maker"
      - "influencer"
    lead_score_rules:
      industry_match: 30
      keyword_match: 20
      company_size_fit: 10
      decision_maker_found: 25
      verified_contact_present: 15
    search_frequency: "Weekly"
    priority: 2

  - product_name: "GFRP Rebar"
    enabled: true
    country: ["India"]
    regions: ["Pan India"]
    target_industries:
      - "EPC Contractors"
      - "Infrastructure Contractors"
      - "Highway Contractors"
      - "Bridge Construction Companies"
      - "Metro Rail Contractors"
      - "Tunnel Construction Companies"
      - "Industrial Construction Companies"
      - "Commercial Builders"
      - "Government Contractors"
      - "Water Treatment Infrastructure Companies"
    exclude_industries:
      - "Rebar Manufacturers"
      - "Construction Material Suppliers"
    company_keywords:
      - "epc"
      - "infrastructure"
      - "contractor"
      - "highway"
      - "bridge"
      - "metro rail"
      - "tunnel"
      - "construction"
      - "water treatment"
    exclude_keywords:
      - "supplier"
      - "manufacturer"
    apollo_filters:
      seniority: ["manager", "director", "vp", "head", "owner"]
      department: ["projects", "procurement", "engineering", "construction"]
      company_status: ["active"]
    employee_min: 50
    employee_max: 20000
    company_size: ["medium", "large", "enterprise"]
    preferred_company_types:
      - "construction"
      - "infrastructure"
      - "epc"
    target_titles:
      - "Project Manager"
      - "Procurement Manager"
      - "Purchase Manager"
      - "Structural Engineer"
      - "Civil Engineer"
      - "Construction Manager"
      - "Engineering Manager"
    preferred_titles:
      - "Project Manager"
      - "Procurement Manager"
      - "Construction Manager"
    decision_level:
      - "decision maker"
      - "influencer"
    lead_score_rules:
      industry_match: 30
      keyword_match: 20
      company_size_fit: 10
      decision_maker_found: 25
      verified_contact_present: 15
    search_frequency: "Monthly"
    priority: 3
```

### Schema Notes

- `enabled` allows a product line to be turned off without code changes.
- `exclude_industries` and `exclude_keywords` prevent competitor or supplier capture.
- `apollo_filters` is a provider-facing block for query shaping.
- `preferred_company_types` and `preferred_titles` help ranking and scoring.
- `decision_level` describes how close a contact is to the buying decision.
- `search_frequency` controls scheduler cadence.
- `priority` resolves conflicts when a record matches multiple product lines.

---

## 4. Provider Interface

The discovery engine should depend on a provider interface, not Apollo directly.

### Provider Responsibilities

The provider interface should support:

- organization search
- people search
- optional retrieval of provider metadata such as last updated timestamps
- provider-normalized error handling
- rate-limit awareness

### Suggested Interface Contract

- `search_organizations(icp) -> list[RawOrganizationResult]`
- `search_people(organization, icp) -> list[RawPersonResult]`
- `provider_name() -> str`
- `health_check() -> ProviderHealth`

### Normalized Provider Output

The provider should return normalized raw records with fields like:

- provider_id
- provider_name
- source_payload
- company_name
- company_domain
- company_industry
- company_size
- employee_count
- country
- region
- last_updated
- person_name
- title
- email
- phone
- linkedin_url
- confidence

The provider should not decide qualification or CRM merge policy.
It only returns data.

---

## 5. Apollo Provider Responsibilities

Apollo is the only implementation today.
Its job is to translate the provider contract into Apollo API calls.

### Responsibilities

- call Apollo Organization Search
- call Apollo People Search
- map Apollo fields into normalized provider records
- respect Apollo rate limits
- respect `APOLLO_DAILY_CALL_LIMIT`
- respect `APOLLO_MIN_SECONDS_BETWEEN_CALLS`
- retry transient API failures up to `APOLLO_RETRY_LIMIT`
- return blank values for missing fields
- never scrape or infer from websites

### Apollo Provider Rules

- Apollo is a source, not the system architecture.
- Apollo-specific logic stays in the Apollo provider layer.
- Discovery, qualification, and CRM import remain provider-agnostic.

---

## 6. Scheduler Workflow

The scheduler should:

1. Load the ICP YAML configuration.
2. Filter to enabled product lines.
3. Determine which product lines are due based on `search_frequency`.
4. For each due product line:
   - create a run record
   - initialize counters
   - call the discovery engine
5. Persist run metrics when complete.

### Frequency Rules

- Daily means run once per day.
- Weekly means run once per week.
- Monthly means run once per month.

The scheduler should respect per-ICP frequency rather than one global cadence.

---

## 7. Qualification Flow

The qualification flow should occur after raw discovery results are collected and before CRM import.

### Qualification Steps

1. Validate required provider fields.
2. Check target industry match.
3. Check keyword match and exclude lists.
4. Check company size thresholds.
5. Check whether a relevant contact exists.
6. Score the record using the ICP rule weights.
7. Determine whether the result is:
   - qualified
   - needs manual review
   - rejected

### Manual Review Rule

If Apollo data is insufficient to qualify confidently:

- do not import immediately
- mark the company as `needs_manual_review`
- retain the raw discovery result for later inspection

No alternate scraping or enrichment source should be used to fill the gap.

---

## 8. Duplicate Merge Flow

The current dedupe logic remains the source of truth.
The Phase 2 pipeline should call the existing merge behavior rather than invent a new one.

### Company Merge Rules

If a company already exists:

- update only missing fields
- never overwrite values that were manually edited
- store Apollo identifiers if missing
- add an audit event for every merged field

### Contact Merge Rules

If a contact already exists:

- update only missing Apollo fields
- preserve manual edits
- store Apollo identifiers if missing
- add an audit event for every merged field

### Merge Principle

The CRM should converge on a richer record over time, but human edits should always win over provider defaults.

---

## 9. Discovery Metrics

Each discovery run must create a run record with:

- Run ID
- Start Time
- End Time
- Duration
- Companies Found
- Companies Imported
- Companies Updated
- Companies Skipped
- Contacts Found
- Contacts Imported
- Contacts Updated
- Contacts Skipped
- API Calls Used
- Quota Remaining
- Errors
- Warnings
- Status

These metrics should later power operational dashboards and quota monitoring.

---

## 10. Database Changes

This section defines future schema needs only. No migration should be written yet.

### Company Fields to Add

- apollo_organization_id
- apollo_last_updated
- last_sync
- sync_status
- needs_manual_review
- owner
- status
- assigned_date
- assignment_source
- lead_score

### Contact Fields to Add

- apollo_person_id
- verification_status
- last_sync
- lead_score

### Discovery Run Fields to Add

- run_id
- start_time
- end_time
- duration
- companies_found
- companies_imported
- companies_updated
- companies_skipped
- contacts_found
- contacts_imported
- contacts_updated
- contacts_skipped
- api_calls_used
- quota_remaining
- errors
- warnings
- status

### Notes

- Owner may be NULL initially.
- User management is not part of Phase 2A.
- Assignment support is schema preparation only.

---

## 11. API Changes

No API should be written yet, but the design should prepare for these endpoints.

### Likely Future Endpoints

- `GET /discovery/runs`
- `GET /discovery/runs/{id}`
- `GET /discovery/summary`
- `GET /discovery/manual-review`
- `POST /discovery/runs/{id}/retry`
- `POST /discovery/icp/reload`
- `GET /icp`

### Behavioral Notes

- API should expose discovery metrics.
- API should show manual-review records.
- API should not expose provider secrets.
- API should not bypass Phase 1 auth rules.

---

## 12. Sequence Diagrams

### Discovery Sequence

```text
Scheduler
  -> Discovery Engine
    -> ICP Engine
    -> Provider Interface
      -> Apollo Provider
        -> Organization Search
        -> People Search
    -> Qualification Engine
    -> Duplicate Detection
    -> CRM Import
    -> Audit
    -> Run Metrics
```

### Manual Review Sequence

```text
Discovery Engine
  -> Apollo Provider
  -> Qualification Engine
  -> Incomplete Confidence
  -> Mark Needs Manual Review
  -> Store Run Metrics
```

### Merge Sequence

```text
Provider Result
  -> Existing CRM Record Found
  -> Merge Missing Fields Only
  -> Preserve Manual Edits
  -> Write Audit Event
  -> Update Sync Metadata
```

---

## 13. Error Handling Strategy

### Provider Errors

- Treat provider timeouts as retryable.
- Treat rate-limit responses as retryable with backoff.
- Treat invalid credentials as fatal and report immediately.
- Treat malformed provider payloads as non-fatal for the whole run if they affect only one record.

### Qualification Errors

- If scoring fails for one record, isolate the failure.
- Mark the record for manual review.
- Continue processing remaining records.

### Import Errors

- If a duplicate merge fails, keep the original CRM record intact.
- Log the failure in the run record.
- Add an audit entry if partial changes were applied.

### Run-Level Errors

- A single run should not collapse the whole system.
- A failed run should still persist errors, warnings, and partial metrics.

---

## 14. Retry Strategy

### Retry Rules

- Retry transient Apollo failures up to `APOLLO_RETRY_LIMIT`.
- Use exponential backoff.
- Respect `APOLLO_MIN_SECONDS_BETWEEN_CALLS`.
- Do not retry on validation failures or permission failures.

### Retry Boundaries

- Retry at the provider boundary, not inside the CRM import layer.
- Keep retries small and bounded so the scheduler does not overrun its window.

---

## 15. Rate Limiting Strategy

The scheduler and provider layer should respect these environment variables:

- `APOLLO_DAILY_CALL_LIMIT`
- `APOLLO_MAX_COMPANIES_PER_RUN`
- `APOLLO_MAX_CONTACTS_PER_COMPANY`
- `APOLLO_MIN_SECONDS_BETWEEN_CALLS`
- `APOLLO_RETRY_LIMIT`

### Rules

- Stop making Apollo calls when the daily limit is reached.
- Stop a run when the per-run company limit is reached.
- Stop contact enumeration for a company when the per-company contact limit is reached.
- Pause between provider calls using the minimum seconds setting.
- Record quota remaining in the run metrics.

---

## 16. Audit Strategy

Audit events should be written for all material changes.

### Auditable Actions

- auto-created company
- auto-updated company
- auto-created contact
- auto-updated contact
- merged Apollo field
- marked manual review
- imported qualified lead
- run started
- run completed
- run failed

### Audit Content

- entity type
- entity id
- action
- reason
- provider metadata
- merge metadata
- run metadata

Audit logging should preserve why a record changed and where the data came from.

---

## 17. Future Extensibility

This design should leave room for future growth without forcing a rewrite.

### Future Providers

- The provider interface allows adding another data source later.
- Apollo remains the only implementation today.

### Future Sales Users

- Owner and assignment fields are prepared for multi-user routing.
- User management itself is deferred.

### Future Automation

- Batch approval
- Draft generation
- Follow-up scheduling
- Slack or email digests

### Future Analytics

- funnel conversion by product line
- discovery quota usage
- qualification rates
- manual-review rates
- average score by ICP

---

## Why This Architecture Is Better

- It keeps Apollo isolated behind a provider abstraction.
- It avoids hardcoding business rules into the scheduler.
- It makes ICP changes data-driven through YAML.
- It prevents low-confidence data from polluting the CRM.
- It preserves human edits while still benefiting from automation.
- It sets up a clean path to multiple sales users later.
- It adds observability through run metrics and audit logs.
- It keeps Phase 1 stable while expanding capability in a controlled way.

---

## Risks

- Apollo rate limits or data quality may reduce discovery coverage.
- A richer ICP schema increases operational complexity.
- Manual review queues can grow if Apollo data is incomplete.
- Merge rules need careful testing to avoid overwriting valuable manual edits.
- Scheduled discovery may produce noisy results if ICP keywords are too broad.
- Additional schema fields will require disciplined migration management.

---

## Assumptions

- Apollo remains the only automated provider for Phase 2A and beyond for now.
- Existing Phase 1 dedupe logic will remain the merge baseline.
- Manual review is acceptable when Apollo data is incomplete.
- The initial deployment still runs on a single backend instance.
- User management is not needed yet, only schema preparation for ownership.
- The YAML file will be the initial source of truth for ICP definitions.

---

## Approval Gate

This document defines the revised design only.
No models, migrations, APIs, or runtime code should be written until approval is given to proceed with Phase 2A.
