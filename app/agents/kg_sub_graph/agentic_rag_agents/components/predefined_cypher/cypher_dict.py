from typing import Dict

predefined_cypher_dict: Dict[str, str] = {
    # 产品类查询
    "product_by_name": "MATCH (p:Product) WHERE p.ProductName CONTAINS $product_name RETURN p.ProductName, p.UnitPrice, p.UnitsInStock, p.CategoryName",
    "product_by_category": "MATCH (p:Product)-[:BELONGS_TO]->(c:Category) WHERE c.CategoryName = $category_name RETURN p.ProductName, p.UnitPrice, p.UnitsInStock",
    "product_by_supplier": "MATCH (p:Product)-[:SUPPLIED_BY]->(s:Supplier) WHERE s.CompanyName = $supplier_name RETURN p.ProductName, p.UnitPrice, p.UnitsInStock",
    "products_low_stock": "MATCH (p:Product) WHERE toInteger(p.UnitsInStock) < 10 RETURN p.ProductName, p.UnitsInStock, p.CategoryName ORDER BY toInteger(p.UnitsInStock)",
    "products_popular": "MATCH (p:Product)<-[:ABOUT]-(r:Review) RETURN p.ProductName, count(r) as ReviewCount, avg(toFloat(r.Rating)) as AvgRating ORDER BY ReviewCount DESC LIMIT 10",
    
    # 客户类查询
    "customer_by_name": "MATCH (c:Customer) WHERE c.CompanyName CONTAINS $customer_name RETURN c.CompanyName, c.ContactName, c.Phone, c.Country",
    "customer_orders": "MATCH (c:Customer)-[:PLACED]->(o:Order) WHERE c.CompanyName = $customer_name RETURN o.orderId, o.OrderDate, o.ShippedDate",
    "customer_purchase_history": "MATCH (c:Customer)-[:PLACED]->(o:Order)-[:CONTAINS]->(p:Product) WHERE c.CompanyName = $customer_name RETURN p.ProductName, o.OrderDate, p.UnitPrice",
    
    # 订单类查询
    "order_by_id": "MATCH (o:Order) WHERE o.orderId = $order_id RETURN o.OrderDate, o.RequiredDate, o.ShippedDate, o.CustomerName",
    "order_details": "MATCH (o:Order)-[contains:CONTAINS]->(p:Product) WHERE o.orderId = $order_id RETURN p.ProductName, contains.Quantity, contains.UnitPrice, toFloat(contains.Quantity) * toFloat(contains.UnitPrice) as TotalPrice",
    "recent_orders": "MATCH (o:Order) RETURN o.orderId, o.OrderDate, o.CustomerName ORDER BY o.OrderDate DESC LIMIT 10",
    "delayed_orders": "MATCH (o:Order) WHERE o.RequiredDate < o.ShippedDate OR (o.RequiredDate < date() AND o.ShippedDate IS NULL) RETURN o.orderId, o.OrderDate, o.RequiredDate, o.ShippedDate, o.CustomerName",
    
    # 供应商类查询
    "supplier_by_country": "MATCH (s:Supplier) WHERE s.Country = $country RETURN s.CompanyName, s.ContactName, s.Phone",
    "supplier_products": "MATCH (s:Supplier)<-[:SUPPLIED_BY]-(p:Product) WHERE s.CompanyName = $supplier_name RETURN p.ProductName, p.UnitPrice, p.UnitsInStock",
    
    # 类别类查询
    "all_categories": "MATCH (c:Category) RETURN c.CategoryName, c.Description",
    "category_products": "MATCH (c:Category)<-[:BELONGS_TO]-(p:Product) WHERE c.CategoryName = $category_name RETURN p.ProductName, p.UnitPrice, p.UnitsInStock",
    "category_product_count": "MATCH (c:Category)<-[:BELONGS_TO]-(p:Product) RETURN c.CategoryName, count(p) as ProductCount ORDER BY ProductCount DESC",
    
    # 员工类查询
    "employee_by_name": "MATCH (e:Employee) WHERE e.FirstName + ' ' + e.LastName CONTAINS $employee_name RETURN e.FirstName, e.LastName, e.Title, e.HireDate",
    "employee_processed_orders": "MATCH (e:Employee)-[:PROCESSED]->(o:Order) WHERE e.FirstName + ' ' + e.LastName = $employee_name RETURN o.orderId, o.OrderDate, o.CustomerName",
    
    # 评论类查询
    "product_reviews": "MATCH (p:Product)<-[:ABOUT]-(r:Review) WHERE p.ProductName = $product_name RETURN r.CustomerName, r.Rating, r.ReviewText, r.ReviewDate ORDER BY r.ReviewDate DESC",
    "top_rated_products": "MATCH (p:Product)<-[:ABOUT]-(r:Review) WITH p.ProductName as ProductName, avg(toFloat(r.Rating)) as AvgRating, count(r) as ReviewCount WHERE ReviewCount > 3 RETURN ProductName, AvgRating, ReviewCount ORDER BY AvgRating DESC LIMIT 10",
    
    # 销售分析类查询
    "product_sales": "MATCH (o:Order)-[c:CONTAINS]->(p:Product) WHERE p.ProductName = $product_name RETURN sum(toFloat(c.Quantity) * toFloat(c.UnitPrice)) as TotalSales",
    "category_sales": "MATCH (o:Order)-[c:CONTAINS]->(p:Product)-[:BELONGS_TO]->(cat:Category) RETURN cat.CategoryName, sum(toFloat(c.Quantity) * toFloat(c.UnitPrice)) as TotalSales ORDER BY TotalSales DESC",
    "monthly_sales": "MATCH (o:Order)-[c:CONTAINS]->(p:Product) RETURN substring(o.OrderDate, 0, 7) as Month, sum(toFloat(c.Quantity) * toFloat(c.UnitPrice)) as Sales ORDER BY Month",
    
    # 智能家居相关查询（示例）
    "smart_home_products": "MATCH (p:Product)-[:BELONGS_TO]->(c:Category) WHERE c.CategoryName CONTAINS '智能' RETURN p.ProductName, p.UnitPrice, p.UnitsInStock, c.CategoryName",
    "smart_speakers": "MATCH (p:Product)-[:BELONGS_TO]->(c:Category) WHERE c.CategoryName = '智能音箱' RETURN p.ProductName, p.UnitPrice, p.UnitsInStock",
    "smart_lighting": "MATCH (p:Product)-[:BELONGS_TO]->(c:Category) WHERE c.CategoryName = '智能照明' RETURN p.ProductName, p.UnitPrice, p.UnitsInStock"
}