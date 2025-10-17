# Quick Start Guide: Using Variables in NeuroDB

## What are Variables?

Variables let you save values that you can reuse across multiple queries using the `{{variable_name}}` syntax.

## Adding a Variable

1. Look at the left sidebar (Schema Browser)
2. Find the **"Variables"** section (below Saved Queries)
3. Click the **➕** button
4. Enter a variable name (e.g., `start_date`, `user_id`)
5. Enter the value (e.g., `2024-01-01`, `12345`)
6. Click **"Add Variable"**

## Using Variables in Queries

### Method 1: Type Manually
```sql
SELECT * FROM users WHERE created_at > '{{start_date}}';
```

### Method 2: Use Autocomplete
1. Type `{{` in your query
2. Autocomplete popup shows all your variables
3. Use ↑↓ arrows to select
4. Press Tab or Enter to insert

## Example Workflow

### Step 1: Create Variables
```
Variable Name: start_date
Value: 2024-01-01

Variable Name: end_date
Value: 2024-12-31

Variable Name: user_status
Value: active
```

### Step 2: Write Query
```sql
SELECT 
    user_id,
    username,
    created_at,
    status
FROM users
WHERE created_at BETWEEN '{{start_date}}' AND '{{end_date}}'
  AND status = '{{user_status}}'
ORDER BY created_at DESC;
```

### Step 3: Execute
- Click **▶** to run the query
- Variables are automatically substituted
- Results appear below

### What Actually Runs:
```sql
SELECT 
    user_id,
    username,
    created_at,
    status
FROM users
WHERE created_at BETWEEN '2024-01-01' AND '2024-12-31'
  AND status = 'active'
ORDER BY created_at DESC;
```

## Managing Variables

### Copy Variable Value
- Click the **📋** button next to the variable
- Value is copied to clipboard

### Copy Variable Placeholder
- **Double-click** the variable name
- `{{variable_name}}` is copied to clipboard
- Paste it into your query

### Edit Variable
- **Right-click** on variable
- Select **"✏️ Edit Variable"**
- Enter new value
- Click OK

### Delete Variable
- Click the **🗑️** button next to the variable
- Confirm deletion

## Practical Use Cases

### 1. Testing Different Date Ranges
```sql
-- Change start_date and end_date variables to test different periods
SELECT COUNT(*) FROM orders
WHERE order_date BETWEEN '{{start_date}}' AND '{{end_date}}';
```

### 2. Pagination
```sql
-- Change page_size and page_offset to browse through results
SELECT * FROM products
ORDER BY id
LIMIT {{page_size}} OFFSET {{page_offset}};
```

### 3. User-Specific Queries
```sql
-- Change user_id to test different users
SELECT * FROM user_activity
WHERE user_id = {{user_id}}
ORDER BY timestamp DESC;
```

### 4. Environment-Specific Values
```sql
-- Set different table_prefix for dev/staging/prod
SELECT * FROM {{table_prefix}}_users;
```

## Tips & Tricks

✅ **Use descriptive names**: `user_id` is better than `id1`  
✅ **Keep values up-to-date**: Edit variables instead of rewriting queries  
✅ **Test with different values**: Quickly swap values to test edge cases  
✅ **Combine with saved queries**: Save queries with variables for maximum reusability  

⚠️ **Missing Variables**: If you use `{{undefined_var}}`, you'll get a warning before execution

## Advanced: Variable Naming Conventions

```
✅ Good names:
- start_date
- end_date
- user_id
- page_size
- table_name
- status_filter

❌ Avoid:
- x, y, z (not descriptive)
- temp, tmp (what is it?)
- variable1, variable2 (use meaningful names)
```

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Start variable autocomplete | Type `{{` |
| Navigate suggestions | ↑ / ↓ |
| Accept suggestion | Tab or Enter |
| Close autocomplete | Esc |
| Copy as placeholder | Double-click variable |

## Where are Variables Stored?

Variables are saved in:
- **macOS/Linux**: `~/.config/pgwarp/saved_variables.json`
- **Windows**: `%APPDATA%\PgWarp\saved_variables.json`

They persist between sessions and are independent of database connections.

---

**Happy Querying! 🚀**
