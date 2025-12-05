---
description: Fix Database Schema Issues (Missing Columns)
---

The error `column users.membership_type does not exist` means your database tables are older than your code. You need to update the database schema.

1.  **Open your terminal** in the project directory (`c:\Users\rakib\library-management-system`).

2.  **Initialize Migrations** (if not already done):
    ```bash
    flask db init
    ```
    *(If this says "directory already exists", skip to step 3)*

3.  **Generate Migration Script**:
    ```bash
    flask db migrate -m "Add membership columns"
    ```

4.  **Apply Changes to Database**:
    ```bash
    flask db upgrade
    ```

5.  **Restart your server**:
    Stop the current server (Ctrl+C) and run:
    ```bash
    python run.py
    ```

**Troubleshooting:**
If `flask db migrate` fails or says "Target database is not up to date", verify that there are no pending migrations. If this is a development database and you don't care about the data, you can reset it completely (DANGEROUS: deletes all data):
1.  Connect to your database tool or simply recreate the tables if you have a script.
2.  Or delete the `migrations` folder and drop the tables manually, then run steps 2-4.
