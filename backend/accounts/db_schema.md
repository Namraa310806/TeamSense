# Database Schema (Multi-Organization, RBAC)

## Organization
- organization_id: UUID (PK)
- organization_name: string
- industry: string
- created_by: FK(User)
- created_at: datetime

## Profile (User Extension)
- user: FK(User, PK)
- role: enum (ADMIN, EXECUTIVE, HR)
- organization: FK(Organization, nullable)
- designation: string
- department: string

## Employee
- id: PK
- name: string
- role: string
- department: string
- join_date: date
- organization: FK(Organization)
- manager: string (legacy)
- manager_user: FK(User, nullable)
- hr_owner: FK(User, nullable)
- email: string (unique)
- created_at: datetime
- updated_at: datetime
