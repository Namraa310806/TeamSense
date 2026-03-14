# Multi-Organization & RBAC API Endpoints

## Authentication
- POST `/api/token/` — Obtain JWT
- POST `/api/token/refresh/` — Refresh JWT

## User Profile
- GET `/api/accounts/me/` — Get current user profile & role

## Organization
- GET `/api/accounts/organizations/` — List organizations (Admin only)
- POST `/api/accounts/organizations/` — Create organization (Executive/Admin)
- GET `/api/accounts/organizations/{id}/` — Retrieve organization
- PATCH `/api/accounts/organizations/{id}/` — Update organization (Admin/Executive)
- DELETE `/api/accounts/organizations/{id}/` — Delete organization (Admin)

## Employee
- GET `/api/employees/` — List employees (HR: own org, Executive: own org, Admin: all)
- POST `/api/employees/` — Create employee (HR/Executive)
- GET `/api/employees/{id}/` — Retrieve employee (HR: own org, Executive: own org, Admin: all)
- PATCH `/api/employees/{id}/` — Update employee (HR/Executive)
- DELETE `/api/employees/{id}/` — Delete employee (HR/Executive)

## Analytics
- GET `/api/dashboard/` — Org-level analytics (Executive/HR: own org, Admin: all)
- GET `/api/employee-insights/{id}/` — Employee AI insights (HR/Executive: own org, Admin: all)
- GET `/api/attrition/{id}/` — Employee attrition risk (HR/Executive: own org, Admin: all)

## Meetings
- POST `/api/meetings/upload/` — Upload meeting transcript (HR/Executive: own org)
- GET `/api/meetings/` — List meetings (HR/Executive: own org, Admin: all)
- GET `/api/meetings/{id}/` — Meeting detail (HR/Executive: own org, Admin: all)
