# Business Rules

## Lead Lock

- lock window: `60 days`
- active lock statuses:
  - `Qualified`
  - `Contacted`
- converted leads should not reopen the same opportunity in `User Lookup`

## Lead Statuses

- `Qualified`
- `Contacted`
- `Converted`
- `Rejected`
- `Expired`

## Eligibility by Product

### Quick

- audience-driven
- excludes users already using Quick
- excludes users rejected by risk matrix

### Future Fund

- audience-driven
- excludes users with existing Future Fund usage

### Tapi

- segment-driven
- excludes users with utilities payment usage

### e-Sim

- broad contractor audience
- excludes users with existing e-Sim usage

### Reserve

- pending business validation
- do not redefine logic without confirmation from stakeholders

## MRR

Estimated MRR per product:

- `Quick`: `11.9`
- `Future Fund`: `3.0`
- `Reserve`: `14.9`
- `Tapi`: `1.6`
- `e-Sim`: `5.0`

Current dashboard rule:

- MRR is counted only for `Converted` leads

## Admin Actions

Admins can:

- delete leads from `Dashboard`

Admin access is controlled by configured allowlist emails.
