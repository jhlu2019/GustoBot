"""预定义Cypher查询的描述信息

此模块包含了所有预定义Cypher查询的详细描述，用于增强向量匹配的准确性。
描述应当包含查询的目的、适用场景和可能的用户问法。
"""

# 产品类查询描述
PRODUCT_QUERY_DESCRIPTIONS = {
    "product_by_name": "查询特定名称的产品信息，包括价格、库存和类别。适用于用户询问某个具体产品的详细信息。",
    "product_by_category": "查询特定类别下的所有产品信息。适用于用户想了解某个产品类别下有哪些商品。",
    "product_by_supplier": "查询特定供应商提供的所有产品。适用于用户想了解某个供应商提供了哪些商品。",
    "products_low_stock": "查询库存不足（低于10个）的产品信息。适用于用户询问哪些产品需要补货或库存紧张。",
    "products_popular": "查询最受欢迎的产品（基于评论数量）。适用于用户询问哪些产品最受欢迎或销量最好。",
}

# 客户类查询描述
CUSTOMER_QUERY_DESCRIPTIONS = {
    "customer_by_name": "查询特定客户的详细信息。适用于用户询问某个客户的联系方式或地址。",
    "customer_orders": "查询特定客户的所有订单信息。适用于用户询问某个客户的订单历史。",
    "customer_purchase_history": "查询特定客户的购买历史，包括购买的产品和日期。适用于用户询问客户购买了哪些产品。",
}

# 订单类查询描述
ORDER_QUERY_DESCRIPTIONS = {
    "order_by_id": "查询特定订单ID的基本信息。适用于用户询问某个订单的状态、日期等。",
    "order_details": "查询特定订单的详细信息，包括包含的产品、数量和价格。适用于用户询问订单中包含哪些商品。",
    "recent_orders": "查询最近的10个订单。适用于用户询问最近有哪些新订单。",
    "delayed_orders": "查询延迟发货的订单。适用于用户询问哪些订单发货延迟或未按时发货。",
}

# 供应商类查询描述
SUPPLIER_QUERY_DESCRIPTIONS = {
    "supplier_by_country": "查询特定国家的所有供应商。适用于用户询问某个国家有哪些供应商。",
    "supplier_products": "查询特定供应商提供的所有产品。适用于用户询问某个供应商提供了哪些产品。",
}

# 类别类查询描述
CATEGORY_QUERY_DESCRIPTIONS = {
    "all_categories": "查询所有产品类别及其描述。适用于用户询问有哪些产品类别。",
    "category_products": "查询特定类别下的所有产品。适用于用户询问某个类别下有哪些产品。",
    "category_product_count": "查询每个类别包含的产品数量。适用于用户询问各类别的产品数量分布。",
}

# 员工类查询描述
EMPLOYEE_QUERY_DESCRIPTIONS = {
    "employee_by_name": "查询特定员工的基本信息。适用于用户询问某个员工的职位、入职日期等。",
    "employee_processed_orders": "查询特定员工处理的所有订单。适用于用户询问某个员工处理了哪些订单。",
}

# 评论类查询描述
REVIEW_QUERY_DESCRIPTIONS = {
    "product_reviews": "查询特定产品的所有评论。适用于用户询问某个产品的用户评价。",
    "top_rated_products": "查询评分最高的产品。适用于用户询问哪些产品评分最高或最受好评。",
}

# 销售分析类查询描述
SALES_QUERY_DESCRIPTIONS = {
    "product_sales": "查询特定产品的总销售额。适用于用户询问某个产品的销售情况或销售额。",
    "category_sales": "查询各产品类别的总销售额。适用于用户询问哪些类别销售额最高或各类别的销售情况。",
    "monthly_sales": "查询每月的销售情况。适用于用户询问销售额的月度变化或趋势。",
}

# 智能家居相关查询描述
SMART_HOME_QUERY_DESCRIPTIONS = {
    "smart_home_products": "查询所有智能家居相关产品。适用于用户询问有哪些智能家居产品。",
    "smart_speakers": "查询所有智能音箱类产品。适用于用户询问有哪些智能音箱或语音助手产品。",
    "smart_lighting": "查询所有智能照明类产品。适用于用户询问有哪些智能灯或智能照明产品。",
}

# 合并所有查询描述
QUERY_DESCRIPTIONS = {}
QUERY_DESCRIPTIONS.update(PRODUCT_QUERY_DESCRIPTIONS)
QUERY_DESCRIPTIONS.update(CUSTOMER_QUERY_DESCRIPTIONS)
QUERY_DESCRIPTIONS.update(ORDER_QUERY_DESCRIPTIONS)
QUERY_DESCRIPTIONS.update(SUPPLIER_QUERY_DESCRIPTIONS)
QUERY_DESCRIPTIONS.update(CATEGORY_QUERY_DESCRIPTIONS)
QUERY_DESCRIPTIONS.update(EMPLOYEE_QUERY_DESCRIPTIONS)
QUERY_DESCRIPTIONS.update(REVIEW_QUERY_DESCRIPTIONS)
QUERY_DESCRIPTIONS.update(SALES_QUERY_DESCRIPTIONS)
QUERY_DESCRIPTIONS.update(SMART_HOME_QUERY_DESCRIPTIONS) 