# Authentication Flow (JWT)

1. User logs in via `/api/token/` (username/password)
2. Receives JWT access and refresh tokens
3. All API requests include `Authorization: Bearer <token>`
4. JWT decoded, user and profile loaded
5. Permissions checked (role, organization)
6. If valid, access granted; else 403 Forbidden

## Example
- HR user can only access employees in their organization
- Admin can access all organizations
- Executive can manage their org and add HR users
