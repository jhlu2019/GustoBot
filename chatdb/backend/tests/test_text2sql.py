import unittest
from unittest.mock import patch, MagicMock
from app.services.text2sql_service import (
    extract_sql_from_llm_response,
    process_sql_with_value_mappings,
    validate_sql
)


class TestText2SQLService(unittest.TestCase):
    def test_extract_sql_from_llm_response_with_sql_block(self):
        response = """
Here's the SQL query to answer your question:

```sql
SELECT product_name, SUM(quantity * unit_price) as total_sales
FROM products
JOIN order_details ON products.product_id = order_details.product_id
JOIN orders ON orders.order_id = order_details.order_id
WHERE YEAR(order_date) = 2023
GROUP BY product_name
ORDER BY total_sales DESC
LIMIT 5;
```

This query will give you the top 5 products by sales in 2023.
"""
        expected = """SELECT product_name, SUM(quantity * unit_price) as total_sales
FROM products
JOIN order_details ON products.product_id = order_details.product_id
JOIN orders ON orders.order_id = order_details.order_id
WHERE YEAR(order_date) = 2023
GROUP BY product_name
ORDER BY total_sales DESC
LIMIT 5;"""
        
        result = extract_sql_from_llm_response(response)
        self.assertEqual(result, expected)

    def test_extract_sql_from_llm_response_with_code_block(self):
        response = """
Here's the SQL query to answer your question:

```
SELECT product_name, SUM(quantity * unit_price) as total_sales
FROM products
JOIN order_details ON products.product_id = order_details.product_id
JOIN orders ON orders.order_id = order_details.order_id
WHERE YEAR(order_date) = 2023
GROUP BY product_name
ORDER BY total_sales DESC
LIMIT 5;
```

This query will give you the top 5 products by sales in 2023.
"""
        expected = """SELECT product_name, SUM(quantity * unit_price) as total_sales
FROM products
JOIN order_details ON products.product_id = order_details.product_id
JOIN orders ON orders.order_id = order_details.order_id
WHERE YEAR(order_date) = 2023
GROUP BY product_name
ORDER BY total_sales DESC
LIMIT 5;"""
        
        result = extract_sql_from_llm_response(response)
        self.assertEqual(result, expected)

    def test_extract_sql_from_llm_response_with_select_statement(self):
        response = """
To answer your question, you need to run this query:

SELECT product_name, SUM(quantity * unit_price) as total_sales
FROM products
JOIN order_details ON products.product_id = order_details.product_id
JOIN orders ON orders.order_id = order_details.order_id
WHERE YEAR(order_date) = 2023
GROUP BY product_name
ORDER BY total_sales DESC
LIMIT 5;

This query will give you the top 5 products by sales in 2023.
"""
        expected = """SELECT product_name, SUM(quantity * unit_price) as total_sales
FROM products
JOIN order_details ON products.product_id = order_details.product_id
JOIN orders ON orders.order_id = order_details.order_id
WHERE YEAR(order_date) = 2023
GROUP BY product_name
ORDER BY total_sales DESC
LIMIT 5;"""
        
        result = extract_sql_from_llm_response(response)
        self.assertEqual(result, expected)

    def test_process_sql_with_value_mappings(self):
        sql = "SELECT * FROM customers WHERE customer_name = '中石化'"
        value_mappings = {
            "customers.customer_name": {
                "中石化": "中国石化",
                "中石油": "中国石油"
            }
        }
        
        expected = "SELECT * FROM customers WHERE customer_name = '中国石化'"
        result = process_sql_with_value_mappings(sql, value_mappings)
        self.assertEqual(result, expected)

    def test_validate_sql_valid(self):
        sql = "SELECT * FROM customers WHERE customer_id = 1"
        self.assertTrue(validate_sql(sql))

    def test_validate_sql_invalid(self):
        sql = "DROP TABLE customers"
        self.assertFalse(validate_sql(sql))


if __name__ == '__main__':
    unittest.main()
