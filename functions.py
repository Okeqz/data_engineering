"""
functions.py
CampusMart Supplies — Data Engineering Pipeline
All reusable functions: file handling, validation, cleaning,
transformation and reporting.
"""

import csv
import json
import os
from datetime import datetime


# ─────────────────────────────────────────────
# FILE HANDLING
# ─────────────────────────────────────────────

def safe_file_exists(path):
    """
    Check whether a required file exists before the program tries to read it.

    Args:
        path (str): File path to check.

    Returns:
        bool: True if the file exists, False otherwise.
    """
    return os.path.isfile(path)


def ensure_output_folder(path):
    """
    Create the output folder if it does not already exist.

    Args:
        path (str): Directory path to create.
    """
    os.makedirs(path, exist_ok=True)


def read_csv_file(path):
    """
    Read a CSV file and return a list of dictionaries.
    """
    with open(path, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)


def read_json_file(path):
    """
    Read a JSON configuration file.
    """
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def write_csv_file(path, rows, fieldnames):
    """
    Write rows to a CSV file.
    """
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def write_text_file(path, content):
    """
    Write text to a file.
    """
    with open(path, "w", encoding="utf-8") as file:
        file.write(content)


# ─────────────────────────────────────────────
# PARSING AND CLEANING
# ─────────────────────────────────────────────

def parse_int(value):
    """
    Convert a value to an integer.
    Returns None if conversion fails.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def parse_float(value):
    """
    Convert a value to a float.
    Returns None if conversion fails.
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def normalize_date(date_text):
    """
    Convert a date string to YYYY-MM-DD format.
    Accepts YYYY-MM-DD and YYYY/MM/DD.

    Args:
        date_text (str): Raw date string.

    Returns:
        str or None: Normalised date string, or None if unparseable.
    """
    if not date_text:
        return None
    cleaned = str(date_text).strip().replace("/", "-")
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(cleaned, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


# ─────────────────────────────────────────────
# LOOKUP HELPERS
# ─────────────────────────────────────────────

def build_lookup(rows, id_field):
    """
    Build a dictionary keyed by id_field for fast record lookups.

    Args:
        rows (list[dict]): Source records.
        id_field (str): Field to use as the key.

    Returns:
        dict: {id_value: row_dict}
    """
    return {row[id_field].strip(): row for row in rows if id_field in row}


def find_record_by_id(rows, id_field, target_id):
    """
    Search a list of dictionaries and return the first matching record.

    Args:
        rows (list[dict]): List of records to search.
        id_field (str): Dictionary key to match on.
        target_id (str): Value to find.

    Returns:
        dict or None: Matching record, or None if not found.
    """
    for row in rows:
        if row.get(id_field, "").strip() == str(target_id).strip():
            return row
    return None


def get_customer_name(customer):
    """
    Combine first_name and last_name from a customer record.

    Args:
        customer (dict): Customer record dict.

    Returns:
        str: Full name, or empty string if record is None.
    """
    if not customer:
        return ""
    first = customer.get("first_name", "")
    last  = customer.get("last_name",  "")
    return f"{first} {last}"

def calculate_discount(gross_amount, channel, discount_rules):
    """
    Calculate the discount amount.
    """

    rate = discount_rules.get(channel, 0)

    return gross_amount * rate

# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────

def validate_sale_row(sale, customers, products, config, seen_sale_ids):
    """
    Validate a single sale row against business rules.

    Args:
        sale (dict): Raw sale record.
        customers (dict): Customers keyed by customer_id.
        products (dict): Products keyed by product_id.
        config (dict): Configuration with valid channels and discount rules.
        seen_sale_ids (set): Set of already seen sale_ids for uniqueness check.

    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    required_fields = ["sale_id", "customer_id", "product_id", "quantity", "unit_price", "channel", "date"]
    for field in required_fields:
        if field not in sale or not sale[field].strip():
            return False, f"Missing required field: {field}"
        
    if sale["sale_id"] in seen_sale_ids:
        return False, f"Duplicate sale_id: {sale['sale_id']}"
    
    date = normalize_date(sale["date"])
    if not date:
        return False, f"Invalid date format: {sale['date']}"
    
    start_date = config['project_period']['start']
    end_date = config['project_period']['end']
    if not (start_date <= date <= end_date):
        return False, f"Date {date} out of project period ({start_date} to {end_date})"

    quantity = parse_int(sale["quantity"])
    if quantity is None or quantity <= 0:
        return False, f"Invalid quantity: {sale['quantity']}"
    
    price = parse_float(sale["unit_price"])
    if price is None or price <= 0:
        return False, f"Invalid unit_price: {sale['unit_price']}"
    
    if find_record_by_id(customers, "customer_id", sale["customer_id"]) is None:
        return False, f"Unknown customer_id: {sale['customer_id']}"
    
    if find_record_by_id(products, "product_id", sale["product_id"]) is None:
        return False, f"Unknown product_id: {sale['product_id']}"   
    
    valid_channels = config['valid_channels']
    if sale["channel"] not in valid_channels:
        return False, f"Invalid channel: {sale['channel']}"

    seen_sale_ids.add(sale["sale_id"])
    return True, ""

# ─────────────────────────────────────────────
# TRANSFORMATION
# ─────────────────────────────────────────────

def build_rejected_record(source_file, row_number, sale, error_message):
    """
    Build a rejected record entry for reporting.

    Args:
        source_file (str): Name of the source file.
        row_number (int): Row number in the source file.
        sale (dict): Original sale record.
        error_message (str): Reason for rejection.

    Returns:
        dict: Rejected record with metadata.
    """
    return {
        "source_file": source_file,
        "row_number": row_number,
        "sale_id": sale.get("sale_id", ""),
        "date": sale.get("date", ""),
        "error_message": error_message,
        'raw_record': str(sale)
    }

def enrich_sale_record(sale, customers, products, discount_rules):
    """
    Enrich a valid sale record with additional fields.

    Args:
        sale (dict): Validated sale record.
        customers (dict): Customers keyed by customer_id.
        products (dict): Products keyed by product_id.
        discount_rules (dict): Discount rules from configuration.

    Returns:
        dict: Enriched sale record.
    """
    customer = find_record_by_id(customers, "customer_id", sale["customer_id"])
    product = find_record_by_id(products, "product_id", sale["product_id"])

    quantity = parse_int(sale["quantity"])
    unit_price = parse_float(sale["unit_price"])
    total_price = quantity * unit_price

    discount_percentage = discount_rules.get(sale["channel"], 0)
    discount_amount = total_price * (discount_percentage / 100)
    final_price = total_price - discount_amount

    enriched_sale = {
        "sale_id": sale["sale_id"],
        'customer_id': sale["customer_id"],
        "customer_name": get_customer_name(customer),
        'state': customer['state'],
        "product_id": sale["product_id"],
        "product_name": product["product_name"],
        "category": product["category"],
        "quantity": quantity,
        "unit_price": unit_price,
        "channel": sale["channel"],
        "total_price": total_price,
        "discount_percentage": discount_percentage,
        "discount_amount": discount_amount,
        "final_price": final_price,
        "date": normalize_date(sale["date"])
    }

    return enriched_sale

def process_returns(clean_sales, returns):
    """
    Adjust clean sales records based on returns.

    Args:
        clean_sales (list[dict]): List of enriched sales records.
        returns (list[dict]): List of return records.

    Returns:
        list[dict]: Updated list of sales records after processing returns.
    """
    exceptions = []
    sales_lookup = {}
    for sale in clean_sales:
        sales_lookup[sale["sale_id"]] = sale
    for return_row in returns:
        sale_id = return_row.get("sale_id")
        if sale_id not in sales_lookup:
            exceptions.append({
                "sale_id": sale_id,
                "error_message": f"Return references unknown sale_id: {sale_id}",
                "raw_record": str(return_row)
            })
            continue
        sale = sales_lookup[sale_id]
        return_quantity = parse_int(return_row.get("return_quantity"))

        if return_quantity is None or return_quantity <= 0:
            exceptions.append({
                "sale_id": sale_id,
                "error_message": f"Invalid return_quantity: {return_row.get('return_quantity')}",
                "raw_record": str(return_row)
            })
            continue

        already_returned = sale['quantity_returned'] if 'quantity_returned' in sale else 0
        if already_returned + return_quantity > sale['quantity']:
            exceptions.append({
                "sale_id": sale_id,
                "error_message": f"Return quantity exceeds sold quantity. Sold: {sale['quantity']}, Already Returned: {already_returned}, Attempted Return: {return_quantity}",
                "raw_record": str(return_row)
            })
            continue

        returned_value = (return_quantity * sale['unit_price']) * (1 - sale['discount_percentage'] / 100)
        sale['quantity_returned'] +=  return_quantity

        sale['net_quantity'] = sale['quantity'] - sale['quantity_returned']
        sale['net_final_price'] = sale['final_price'] - returned_value

    return clean_sales, exceptions

def build_exceptions_report(exceptions):
    """
    Build a readable exceptions report.
    """

    report = []

    report.append("CampusMart Exceptions Report")
    report.append("=" * 35)
    report.append("")

    if not exceptions:
        report.append("No return exceptions found.")
    else:
        for item in exceptions:
            report.append(f"- {item}")

    return "\n".join(report)

def summarize_by_customer(clean_sales):
    """
    Summarize sales by customer.
    """

    summary = {}

    for sale in clean_sales:

        cid = sale["customer_id"]

        if cid not in summary:
            summary[cid] = {
                "customer_id": cid,
                "customer_name": sale["customer_name"],
                "state": sale["state"],
                "total_orders": 0,
                "total_quantity_purchased": 0,
                "total_quantity_returned": 0,
                "total_net_revenue": 0
            }

        customer = summary[cid]

        customer["total_orders"] += 1
        customer["total_quantity_purchased"] += sale["quantity"]
        customer["total_quantity_returned"] += sale["quantity_returned"]
        customer["total_net_revenue"] += sale["net_amount_after_returns"]

    return list(summary.values())

def build_final_summary(
    clean_sales,
    rejected_count,
    invalid_returns,
    product_summary,
    customer_summary
):

    total_revenue = sum(
        sale["net_amount_after_returns"]
        for sale in clean_sales
    )

    top_product = max(
        product_summary,
        key=lambda x: x["total_net_revenue"]
    )

    top_customer = max(
        customer_summary,
        key=lambda x: x["total_net_revenue"]
    )

    return {
        "valid_sales_count": len(clean_sales),
        "rejected_sales_count": rejected_count,
        "invalid_returns_count": invalid_returns,
        "total_net_revenue": round(total_revenue, 2),

        "top_product_by_revenue": {
            "product_id": top_product["product_id"],
            "product_name": top_product["product_name"],
            "net_revenue": round(
                top_product["total_net_revenue"], 2
            )
        },

        "top_customer_by_revenue": {
            "customer_id": top_customer["customer_id"],
            "customer_name": top_customer["customer_name"],
            "net_revenue": round(
                top_customer["total_net_revenue"], 2
            )
        }
    }

def run_self_checks():

    assert normalize_date("2026/06/03") == "2026-06-03"

    assert calculate_discount(
        10000,
        "online",
        {"online": 0.05}
    ) == 500

    sample = [
        {"customer_id": "C001"}
    ]

    assert find_record_by_id(
        sample,
        "customer_id",
        "C001"
    ) is not None

    print("All self-checks passed.")
    