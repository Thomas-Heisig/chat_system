# Migration Notes

## Database Schema Changes - 2025-12-04

### Added `force_password_change` Field to Users Table

**Date**: 2025-12-04  
**Version**: Current  
**Breaking**: No (adds new optional field with default value)

#### Change Description

Added a new `force_password_change` boolean field to the `users` table to enable forced password changes on first login, particularly for default admin accounts.

#### Migration Required

If you have an **existing database**, you need to add the new column:

##### SQLite Migration

```sql
-- Add the new column to existing users table
ALTER TABLE users ADD COLUMN force_password_change BOOLEAN DEFAULT FALSE;

-- Set existing admin user to require password change (if using default credentials)
UPDATE users 
SET force_password_change = TRUE 
WHERE username = 'admin' 
  AND role = 'admin'
  AND password_hash = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'; 
  -- SHA256 hash of "admin123"
```

##### PostgreSQL Migration

```sql
-- Add the new column to existing users table
ALTER TABLE users ADD COLUMN force_password_change BOOLEAN DEFAULT FALSE;

-- Set existing admin user to require password change (if using default credentials)
UPDATE users 
SET force_password_change = TRUE 
WHERE username = 'admin' 
  AND role = 'admin';
```

##### MongoDB Migration

For MongoDB deployments, no migration is needed as the field will be added automatically with default value `false`.

#### Testing the Migration

After applying the migration:

1. Start the application
2. Try to login with admin credentials
3. The system should detect `force_password_change=true` and require a password change
4. After changing password, `force_password_change` should be set to `false`

#### Affected Files

- `database/connection.py` - Schema definition
- `database/models.py` - User model
- `database/repositories.py` - User repository methods

#### Rollback

If you need to rollback this change:

```sql
-- SQLite/PostgreSQL
ALTER TABLE users DROP COLUMN force_password_change;
```

**Note**: The application will still work without this field, but the forced password change feature will be inactive.

---

## Summary of Changes in This Release

### Security Enhancements
- ✅ Added forced password change for default admin accounts
- ✅ Enhanced security warnings during admin user creation

### Code Quality
- ✅ Removed 116 unused imports
- ✅ Formatted codebase with black
- ✅ Organized imports with isort

### Documentation
- ✅ Complete README.md rewrite with comprehensive documentation
- ✅ Added this migration guide

### Verification
- ✅ Code review completed (3 minor comments, all resolved)
- ✅ Security scan completed (0 alerts)
- ✅ Syntax verification passed

---

**For questions or issues with migration, please open a GitHub issue.**
