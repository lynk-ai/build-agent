**Detect the customer's SQL engine**

The SQL engine is:
```
! bash skills/lynk-build/references/get_engine.sh
```
Keep it in mind throughout all subsequent steps — it informs how you write SQL expressions (e.g. date functions, quoting style, dialect-specific syntax).

**If the engine is not detected, ask the user to provide it**
- If the engine is `unknown`, ask the user: 
"Which SQL engine are you using? (e.g. Snowflake, BigQuery, Redshift, DuckDB, etc.)"
- Once the user answers, make sure the answer makes sense and its a known engine, then write or update `.lynk/config.json` with the value:
  ```json
  {
    "engine": "<user-provided engine>"
  }
  ```
If the `.lynk/config.json` file already exists with other keys, merge — do not overwrite the whole file.
