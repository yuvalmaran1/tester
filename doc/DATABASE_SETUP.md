# Database Configuration Guide

The test framework now supports both SQLite and PostgreSQL databases, including cloud-hosted solutions like Supabase.

## Configuration

The framework uses a single configuration string to specify the database connection. This string is passed to the `TesterConfig` as the `db_config` parameter.

### SQLite Configuration

For SQLite databases, simply provide the file path:

```python
from tester import TesterConfig

cfg = TesterConfig(
    name="MyTester",
    description="Test Framework",
    version="1.0.0",
    db_config="./test_results.db",  # SQLite file path
    setup_file="./setup.json",
    duts_file="./duts.json"
)
```

### PostgreSQL Configuration

For PostgreSQL databases, use a connection string:

```python
from tester import TesterConfig

cfg = TesterConfig(
    name="MyTester",
    description="Test Framework",
    version="1.0.0",
    db_config="postgresql://user:password@localhost:5432/database_name",
    setup_file="./setup.json",
    duts_file="./duts.json"
)
```

### Supabase Configuration

Supabase is built on PostgreSQL, so you can use it with the same connection string format:

```python
from tester import TesterConfig

cfg = TesterConfig(
    name="MyTester",
    description="Test Framework",
    version="1.0.0",
    db_config="postgresql://postgres:your_password@db.abcdefghijklmnop.supabase.co:5432/postgres",
    setup_file="./setup.json",
    duts_file="./duts.json"
)
```

## Environment Variables

For security, it's recommended to use environment variables for database configuration:

```python
import os
from tester import TesterConfig

cfg = TesterConfig(
    name="MyTester",
    description="Test Framework",
    version="1.0.0",
    db_config=os.getenv('DATABASE_URL', './test_results.db'),  # Fallback to SQLite
    setup_file="./setup.json",
    duts_file="./duts.json"
)
```

Set the environment variable:

```bash
# For Supabase
export DATABASE_URL="postgresql://postgres:password@db.project.supabase.co:5432/postgres"

# For local PostgreSQL
export DATABASE_URL="postgresql://user:password@localhost:5432/test_framework"
```

## Examples

### Basic SQLite Example

```python
from tester import Tester, TesterConfig

class MyTester(Tester):
    def __init__(self):
        cfg = TesterConfig(
            name="MyTester",
            description="My Test Framework",
            version="1.0.0",
            db_config="./my_tests.db",  # SQLite
            setup_file="./setup.json",
            duts_file="./duts.json"
        )
        super().__init__(cfg)

    def _init(self, setup):
        return {}

if __name__ == '__main__':
    MyTester()
```

### PostgreSQL/Supabase Example

```python
import os
from tester import Tester, TesterConfig

class MyTester(Tester):
    def __init__(self):
        cfg = TesterConfig(
            name="MyTester",
            description="My Test Framework",
            version="1.0.0",
            db_config=os.getenv('DATABASE_URL', './my_tests.db'),
            setup_file="./setup.json",
            duts_file="./duts.json"
        )
        super().__init__(cfg)

    def _init(self, setup):
        return {}

if __name__ == '__main__':
    MyTester()
```

## Database Setup

### SQLite
No setup required. The database file will be created automatically if it doesn't exist.

### PostgreSQL
1. Install PostgreSQL on your system
2. Create a database for the test framework
3. Create a user with appropriate permissions
4. Use the connection string in your configuration

### Supabase
1. Create a Supabase project at https://supabase.com
2. Go to Settings > Database
3. Copy the connection string
4. Use it in your configuration

## Migration from SQLite to PostgreSQL

If you have existing SQLite data that you want to migrate to PostgreSQL:

1. Export your SQLite data to SQL format
2. Create the PostgreSQL database
3. Import the data using the PostgreSQL client
4. Update your configuration to use the PostgreSQL connection string

## Connection String Parameters

### PostgreSQL Connection String Format
```
postgresql://[user[:password]@][host][:port][/database][?param1=value1&...]
```

### Common Parameters
- `sslmode`: SSL connection mode (require, prefer, disable)
- `connect_timeout`: Connection timeout in seconds
- `application_name`: Application name for logging

### Example with Parameters
```
postgresql://user:password@host:5432/database?sslmode=require&connect_timeout=10
```

## Troubleshooting

### Connection Issues
- Verify the connection string format
- Check network connectivity
- Ensure the database server is running
- Verify user permissions

### SSL Issues (Supabase)
- Ensure `sslmode=require` is included in the connection string
- Check if your system has the required SSL certificates

### Performance
- For PostgreSQL, consider using connection pooling for high-load scenarios
- Monitor database performance and adjust connection limits as needed

## Security Considerations

- Never commit database credentials to version control
- Use environment variables for sensitive information
- Enable SSL for remote database connections
- Regularly rotate database passwords
- Use least-privilege database users
