import re
from app.agents.kg_sub_graph.agentic_rag_agents.retrievers.cypher_examples.base import BaseCypherExampleRetriever
from app.knowledge_base.recipe_kg.question_intent_classifier import QuestionClassifier
from app.knowledge_base.recipe_kg.query_parser_service import QuestionParser

class RecipeCypherRetriever(BaseCypherExampleRetriever):
    """
    菜谱场景的Cypher示例检索器
    复用 recipe_kg 模块的 QuestionClassifier 和 QuestionParser
    结合手工示例，为 LLM 提供高质量的 Cypher 学习样本
    """

    def __init__(self):
        """初始化分类器和解析器"""
        # 不继承Pydantic，直接作为普通Python类使用
        super().__init__()  # 调用父类初始化
        # 使用object.__setattr__避免Pydantic验证
        object.__setattr__(self, '_classifier', QuestionClassifier())
        object.__setattr__(self, '_parser', QuestionParser())

    def get_examples(self, query: str, k: int = 5) -> str:
        """
        根据用户查询返回相关的Cypher查询示例

        策略：
        1. 使用 recipe_kg 的 QuestionClassifier 分类问题
        2. 根据问题类型选择对应类别的示例
        3. 使用 QuestionParser 生成实际的 Cypher 作为参考
        4. 返回最相关的 k 个示例

        Parameters
        ----------
        query : str
            用户的自然语言查询
        k : int, optional
            返回的示例数量, by default 5

        Returns
        -------
        str
            格式化的示例字符串，每个示例包含问题和对应的Cypher查询
        """
        # 使用 recipe_kg 模块分类问题
        classification = self._classifier.classify(query)
        question_type = classification.question_type

        # 按 recipe_kg 的问题类型组织示例模板
        type_based_examples = {
            "recipe_property": [  # 菜谱属性查询
                {
                    "question": "红烧肉怎么做？",
                    "cypher": """MATCH (n:Dish {name: '红烧肉'}) RETURN n.instructions AS 做法"""
                },
                {
                    "question": "红烧肉需要多长时间？",
                    "cypher": """MATCH (n:Dish {name: '红烧肉'}) RETURN n.cook_time AS 耗时"""
                },
                {
                    "question": "红烧肉是什么口味？",
                    "cypher": """MATCH (n:Dish {name: '红烧肉'})-[:HAS_FLAVOR]->(m:Flavor) RETURN collect(m.name) AS 口味"""
                },
                {
                    "question": "宫保鸡丁用什么工艺？",
                    "cypher": """MATCH (n:Dish {name: '宫保鸡丁'})-[:USES_METHOD]->(m:CookingMethod) RETURN collect(m.name) AS 工艺"""
                }
            ],
            "property_constraint": [  # 基于属性的约束查询
                {
                    "question": "有哪些炒菜？",
                    "cypher": """MATCH (dish:Dish)
MATCH (dish)-[:USES_METHOD]->(rel_0:CookingMethod {name: '炒'})
RETURN dish.name AS name LIMIT 15"""
                },
                {
                    "question": "麻辣口味的菜有哪些？",
                    "cypher": """MATCH (dish:Dish)
MATCH (dish)-[:HAS_FLAVOR]->(rel_0:Flavor {name: '麻辣'})
RETURN dish.name AS name LIMIT 15"""
                },
                {
                    "question": "热菜类型的菜品",
                    "cypher": """MATCH (dish:Dish)
MATCH (dish)-[:BELONGS_TO_TYPE]->(rel_0:DishType {name: '热菜'})
RETURN dish.name AS name LIMIT 15"""
                }
            ],
            "relationship_constraint": [  # 关系约束查询
                {
                    "question": "五花肉可以做什么菜？",
                    "cypher": """MATCH (dish:Dish)-[rel:HAS_MAIN_INGREDIENT]->(ingredient:Ingredient {name: '五花肉'})
RETURN type(rel) AS relation, dish.name AS name LIMIT 15"""
                },
                {
                    "question": "用鸡蛋做的菜有哪些？",
                    "cypher": """MATCH (dish:Dish)-[rel:HAS_AUX_INGREDIENT]->(ingredient:Ingredient {name: '鸡蛋'})
RETURN type(rel) AS relation, dish.name AS name LIMIT 15"""
                },
                {
                    "question": "红烧肉需要哪些食材？",
                    "cypher": """MATCH (dish:Dish {name: '红烧肉'})-[rel:HAS_MAIN_INGREDIENT]->(ingredient:Ingredient)
RETURN type(rel) AS relation, ingredient.name AS name"""
                }
            ],
            "relationship_query": [  # 关系用量查询
                {
                    "question": "红烧肉需要多少五花肉？",
                    "cypher": """MATCH (dish:Dish {name: '红烧肉'})-[rel:HAS_MAIN_INGREDIENT]->(ingredient:Ingredient {name: '五花肉'})
RETURN rel.amount_text AS amount_text"""
                },
                {
                    "question": "宫保鸡丁的鸡胸肉用量",
                    "cypher": """MATCH (dish:Dish {name: '宫保鸡丁'})-[rel:HAS_MAIN_INGREDIENT]->(ingredient:Ingredient {name: '鸡胸肉'})
RETURN rel.amount_text AS amount_text"""
                }
            ]
        }

        # 通用补充示例（提供更多样化的查询模式）
        general_examples = [
            {
                "question": "红烧肉的完整烹饪步骤",
                "cypher": """MATCH (d:Dish {name: '红烧肉'})-[r:HAS_STEP]->(s:CookingStep)
RETURN s.order AS 步骤序号, s.instruction AS 步骤说明
ORDER BY s.order"""
            },
            {
                "question": "五花肉的营养价值和功效",
                "cypher": """MATCH (i:Ingredient {name: '五花肉'})
OPTIONAL MATCH (i)-[:HAS_NUTRITION_PROFILE]->(n:NutritionProfile)
OPTIONAL MATCH (i)-[:HAS_HEALTH_BENEFIT]->(h:HealthBenefit)
RETURN i.name, n.description AS 营养, COLLECT(h.name) AS 功效"""
            },
            {
                "question": "麻辣口味的炒菜有哪些？",
                "cypher": """MATCH (d:Dish)-[:HAS_FLAVOR]->(f:Flavor {name: '麻辣'}),
      (d)-[:USES_METHOD]->(m:CookingMethod {name: '炒'})
RETURN d.name AS 菜名 LIMIT 10"""
            },
            {
                "question": "最常用的烹饪方法",
                "cypher": """MATCH (d:Dish)-[:USES_METHOD]->(m:CookingMethod)
WITH m.name AS 方法, COUNT(d) AS 使用次数
RETURN 方法, 使用次数
ORDER BY 使用次数 DESC LIMIT 5"""
            }
        ]

        # 根据问题类型选择示例
        selected_examples = []

        # 1. 优先添加与问题类型匹配的示例
        if question_type and question_type in type_based_examples:
            selected_examples.extend(type_based_examples[question_type])

        # 2. 如果示例不足，添加通用示例
        if len(selected_examples) < k:
            selected_examples.extend(general_examples)

        # 3. 使用 QuestionParser 生成的实际 Cypher 作为首选示例（如果可用）
        try:
            parsed = self._parser.parse({
                "question_type": question_type,
                "args": classification.args
            })
            generated_cyphers = parsed.get("sql", [])
            if generated_cyphers:
                # 将生成的 Cypher 作为第一个示例
                for cypher in generated_cyphers[:1]:  # 只取第一个
                    selected_examples.insert(0, {
                        "question": query,
                        "cypher": cypher
                    })
        except Exception:
            # 如果解析失败，继续使用模板示例
            pass

        # 4. 关键词相关性排序和截取
        def compute_relevance(example, query_text):
            score = 0
            query_words = set(re.findall(r'\w+', query_text.lower()))
            example_words = set(re.findall(r'\w+', example["question"].lower()))

            # 计算单词重叠
            overlap = len(query_words.intersection(example_words))
            score += overlap * 2

            # 关键词匹配加权
            important_keywords = {
                '做法': 3, '怎么做': 3, '步骤': 3,
                '食材': 2, '用量': 2, '多少': 2,
                '口味': 2, '工艺': 2, '类型': 2,
                '营养': 2, '功效': 2
            }
            for keyword, weight in important_keywords.items():
                if keyword in query_text and keyword in example["question"]:
                    score += weight

            return score

        # 排序并选择前 k 个
        scored = [(ex, compute_relevance(ex, query)) for ex in selected_examples]
        scored.sort(key=lambda x: x[1], reverse=True)
        final_examples = [ex for ex, _ in scored[:k]]

        # 5. 格式化输出
        formatted = "\n\n".join([
            f"Question: {ex['question']}\nCypher: {ex['cypher']}"
            for ex in final_examples
        ])

        return formatted
