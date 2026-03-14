# Permission System (RBAC)

## Roles
- ADMIN: Platform-wide access
- EXECUTIVE: Own organization, manage org, add HR users
- HR: Own organization, manage employees, upload meetings, access AI insights

## Enforcement
- API views use custom permissions (IsAdmin, IsExecutive, IsHR, IsSameOrganization)
- Employee, Meeting, Analytics endpoints filter by organization
- Admin can override and access all

## Example
- HR user GET `/api/employees/` returns only employees in their org
- Executive GET `/api/dashboard/` returns analytics for their org
- Admin GET `/api/accounts/organizations/` returns all organizations
