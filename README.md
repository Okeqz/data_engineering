# CampusMart Supplies – Data Engineering Pipeline

## Project Description

This project implements a file-based **Extract, Transform, Load (ETL)** pipeline using only the Python Standard Library (no pandas, NumPy, or other third-party libraries).

The program reads raw CSV and JSON files, validates every sales record against business rules, cleans and enriches valid data, processes customer returns, and generates business reports. The original input files remain unchanged throughout the process.

---

# Required Input Files

Place the following files inside the **`data/`** folder before running the program.

| File            | Description                                             |
| --------------- | ------------------------------------------------------- |
| `sales.csv`     | Raw sales transaction records                                                 |
| `products.csv`  | Product master data and prices                                                  |
| `customers.csv` | Customer master data                                                    |
| `returns.csv`   | Customer return records                                                 |
| `config.json`   | Project period, valid sales channels            and                        discount     rules                                                    |

**Dataset Source**

https://www.kaggle.com/datasets/godekina/campus-mart-data

---

# Project Structure

```
campusmart_project/
│
├── main.py
├── functions.py
├── README.md
├── data/
│   ├── sales.csv
│   ├── products.csv
│   ├── customers.csv
│   ├── returns.csv
│   └── config.json
└── output/
```

---

# How to Run

Open a terminal inside the campusmart project folder and execute:

```bash
python main.py
```

The program automatically:

* Creates the output folder if it does not exist.
* Loads all required input files.
* Validates every sales record.
* Cleans and enriches valid records.
* Processes customer returns.
* Generates all required reports.

No manual editing of file paths is required.

---

# Output Files

| File                      | Description                                                      |
| ------------------------- | ---------------------------------------------------------------- |
| `clean_sales.csv`         | Valid, cleaned and enriched sales records with calculated fields |
| `rejected_rows.csv`       | Invalid sales records with rejection reasons                     |
| `customer_summary.csv`    | Customer purchase summary                                                           |
| `product_performance.csv` | Product sales performance summary                                |
| `exceptions_report.txt`   | Summary of validation and return exceptions                      |
| `final_summary.json`      | Overall project summary in JSON format                           |
| `ingestion_report.txt`    | File loading statistics and validation summary                   |

---

# Main Functions

## File Handling

| Function                                 | Purpose                                                   |
| ---------------------------------------- | --------------------------------------------------------- |
| `safe_file_exists(path)`                 | Check whether a required file exists before reading it.   |
| `ensure_output_folder(path)`             | Create the output directory if it does not already exist. |
| `read_csv_file(path)`                    | Read a CSV file and return a list of dictionaries.        |
| `read_json_file(path)`                   | Read the JSON configuration file.                         |
| `write_csv_file(path, rows, fieldnames)` | Write a list of dictionaries to a CSV file.               |
| `write_text_file(path, content)`         | Write a plain text report file.                           |

## Parsing and Cleaning

| Function                    | Purpose                                           |
| --------------------------- | ------------------------------------------------- |
| `parse_int(value)`          | Safely convert a value to an integer.             |
| `parse_float(value)`        | Safely convert a value to a float.                |
| `normalize_date(date_text)` | Convert supported date formats into `YYYY-MM-DD`. |

## Lookup Helpers

| Function                                       | Purpose                                     |
| ---------------------------------------------- | ------------------------------------------- |
| `build_lookup(rows, id_field)`                 | Build a dictionary for fast record lookups. |
| `find_record_by_id(rows, id_field, target_id)` | Find a record by its unique identifier.     |
| `get_customer_name(customer)`                  | Return a customer's full name.              |

## Validation

| Function                                                              | Purpose                                             |
| --------------------------------------------------------------------- | --------------------------------------------------- |
| `validate_sale_row(sale, customers, products, config, seen_sale_ids)` | Validate a sales record against all business rules. |
| `build_rejected_record(source_file, row_number, sale, error_message)` | Create a rejected sales record for reporting.       |

## Data Transformation

| Function                                                        | Purpose                                                              |
| --------------------------------------------------------------- | -------------------------------------------------------------------- |
| `calculate_discount(gross_amount, channel, discount_rules)`     | Calculate the discount amount for a sale.                            |
| `enrich_sale_record(sale, customers, products, discount_rules)` | Enrich validated sales with customer, product and calculated fields. |
| `process_returns(clean_sales, returns)`                         | Apply valid returns and record invalid return exceptions.            |

## Reporting

| Function                                                                                               | Purpose                                        |
| ------------------------------------------------------------------------------------------------------ | ---------------------------------------------- |
| `build_exceptions_report(exceptions)`                                                                  | Generate a readable exceptions report.         |
| `summarize_by_customer(clean_sales)`                                                                   | Produce customer purchase summaries.           |
| `build_final_summary(clean_sales, rejected_count, invalid_returns, product_summary, customer_summary)` | Create the data used for `final_summary.json`. |

## Testing

| Function            | Purpose                                                                            |
| ------------------- | ---------------------------------------------------------------------------------- |
| `run_self_checks()` | Execute assertion-based tests to verify helper functions before processing begins. |

---

# Assumptions

* The project period is defined in `config.json` using the `project_period` object.
* Dates in either `YYYY-MM-DD` or `YYYY/MM/DD` format are accepted and automatically normalized.
* Sales channels must exactly match one of the values listed in `valid_channels`.
* Customer IDs and Product IDs must exist in their respective reference files.
* Quantities and unit prices must be positive values.
* The first occurrence of a `sale_id` is accepted; subsequent duplicates are rejected.
* Multiple return records may exist for a sale, provided the cumulative returned quantity does not exceed the original quantity sold.
* Invalid return records are recorded in the exceptions report and do not affect sales calculations.
* Full returns are permitted and result in zero remaining quantity and zero net revenue.

---

# Challenges Encountered

| Challenge                     | Solution                                                                                                                |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Inconsistent date formats     | `normalize_date()` converts supported formats to `YYYY-MM-DD`.                                                          |
| Missing required fields       | Validation checks reject incomplete records before processing.                                                          |
| Duplicate sale IDs            | A set of processed sale IDs ensures only the first valid occurrence is accepted.                                        |
| Invalid quantities or prices  | Numeric validation rejects non-positive values.                                                                         |
| Unknown customers or products | Lookup functions verify reference data before enrichment.                                                               |
| Invalid return records        | Return validation prevents unmatched sales and excessive return quantities from affecting reports.                      |
| Program reliability           | Validation errors are recorded in report files so the pipeline continues processing remaining records without crashing. |

---

# Self-Checks

The project includes assertion-based self-checks that verify the correctness of key helper functions before the pipeline begins processing data.

Examples include:

* Date normalization
* Discount calculation
* Customer record lookup

These checks help identify implementation errors early and improve the reliability of the pipeline.

---

# Technologies Used

* Python 3.x
* Standard Library Modules:

  * `csv`
  * `json`
  * `os`
  * `datetime`

No external libraries or frameworks were used.

---

# Author

Oke Queen