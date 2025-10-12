"""
数据验证和清洗模块
Data Validation and Cleaning
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from loguru import logger
import re


class RecipeModel(BaseModel):
    """菜谱数据模型"""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    category: Optional[str] = Field(None, max_length=100)
    cuisine: Optional[str] = Field(None, max_length=100)
    difficulty: Optional[str] = Field(None, max_length=50)
    ingredients: List[str] = Field(default_factory=list)
    steps: List[str] = Field(default_factory=list)
    time: Optional[Dict[str, Any]] = Field(default_factory=dict)
    servings: Optional[str] = Field(None, max_length=50)
    nutrition: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tips: Optional[str] = Field(None, max_length=2000)
    image: Optional[str] = Field(None, max_length=500)
    author: Optional[str] = Field(None, max_length=100)
    source: str = Field(default="Unknown")
    url: Optional[str] = Field(None, max_length=500)

    @validator('name')
    def clean_name(cls, v):
        """清洗菜名"""
        if not v:
            raise ValueError("Recipe name cannot be empty")
        # 移除多余空白
        v = re.sub(r'\s+', ' ', v.strip())
        return v

    @validator('description')
    def clean_description(cls, v):
        """清洗描述"""
        if v:
            v = re.sub(r'\s+', ' ', v.strip())
            # 移除HTML标签
            v = re.sub(r'<[^>]+>', '', v)
        return v

    @validator('ingredients')
    def clean_ingredients(cls, v):
        """清洗食材列表"""
        if not v:
            return []

        cleaned = []
        for ingredient in v:
            if isinstance(ingredient, str):
                # 移除多余空白
                ingredient = re.sub(r'\s+', ' ', ingredient.strip())
                # 移除HTML标签
                ingredient = re.sub(r'<[^>]+>', '', ingredient)
                # 移除特殊字符(保留常用单位和符号)
                ingredient = re.sub(r'[^\w\s\d.,/()（）克毫升勺杯个只片条-]', '', ingredient)

                if ingredient and len(ingredient) > 1:
                    cleaned.append(ingredient)

        return cleaned

    @validator('steps')
    def clean_steps(cls, v):
        """清洗步骤列表"""
        if not v:
            return []

        cleaned = []
        for i, step in enumerate(v, 1):
            if isinstance(step, str):
                # 移除多余空白
                step = re.sub(r'\s+', ' ', step.strip())
                # 移除HTML标签
                step = re.sub(r'<[^>]+>', '', step)

                # 如果步骤没有编号,添加编号
                if not re.match(r'^\d+\.', step):
                    step = f"{i}. {step}"

                if step and len(step) > 3:
                    cleaned.append(step)

        return cleaned

    @validator('url')
    def validate_url(cls, v):
        """验证URL"""
        if v:
            if not v.startswith(('http://', 'https://')):
                return f"https://{v}"
        return v

    class Config:
        # 允许额外字段但不保存
        extra = 'ignore'


class DataValidator:
    """数据验证器"""

    @staticmethod
    def validate(data: Dict) -> Optional[RecipeModel]:
        """
        验证菜谱数据

        Args:
            data: 原始菜谱数据

        Returns:
            验证后的RecipeModel或None
        """
        try:
            recipe = RecipeModel(**data)
            return recipe

        except Exception as e:
            logger.error(f"Validation failed for recipe '{data.get('name', 'Unknown')}': {e}")
            return None

    @staticmethod
    def validate_batch(data_list: List[Dict]) -> List[RecipeModel]:
        """
        批量验证菜谱数据

        Args:
            data_list: 菜谱数据列表

        Returns:
            验证后的RecipeModel列表
        """
        valid_recipes = []
        failed_count = 0

        for data in data_list:
            recipe = DataValidator.validate(data)
            if recipe:
                valid_recipes.append(recipe)
            else:
                failed_count += 1

        logger.info(f"Validated {len(valid_recipes)} recipes, {failed_count} failed")
        return valid_recipes

    @staticmethod
    def clean_text(text: str) -> str:
        """
        清洗文本

        Args:
            text: 原始文本

        Returns:
            清洗后的文本
        """
        if not text:
            return ""

        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)

        # 移除多余空白
        text = re.sub(r'\s+', ' ', text.strip())

        # 移除控制字符
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

        return text

    @staticmethod
    def normalize_time(time_str: str) -> Optional[int]:
        """
        规范化时间字符串为分钟数

        Args:
            time_str: 时间字符串(如: "1小时30分", "PT1H30M", "90 minutes")

        Returns:
            分钟数或None
        """
        if not time_str:
            return None

        try:
            # ISO 8601 duration format (PT1H30M)
            if time_str.startswith('PT'):
                hours = 0
                minutes = 0

                hour_match = re.search(r'(\d+)H', time_str)
                if hour_match:
                    hours = int(hour_match.group(1))

                min_match = re.search(r'(\d+)M', time_str)
                if min_match:
                    minutes = int(min_match.group(1))

                return hours * 60 + minutes

            # 中文格式 (1小时30分钟)
            hours = 0
            minutes = 0

            hour_match = re.search(r'(\d+)\s*[小时時h]', time_str, re.IGNORECASE)
            if hour_match:
                hours = int(hour_match.group(1))

            min_match = re.search(r'(\d+)\s*[分钟鐘m]', time_str, re.IGNORECASE)
            if min_match:
                minutes = int(min_match.group(1))

            if hours or minutes:
                return hours * 60 + minutes

            # 纯数字(假设是分钟)
            num_match = re.search(r'(\d+)', time_str)
            if num_match:
                return int(num_match.group(1))

        except Exception as e:
            logger.warning(f"Failed to normalize time '{time_str}': {e}")

        return None

    @staticmethod
    def extract_difficulty(text: str) -> Optional[str]:
        """
        从文本中提取难度

        Args:
            text: 文本

        Returns:
            难度等级
        """
        text = text.lower()

        if any(word in text for word in ['简单', 'easy', 'simple', '容易']):
            return "简单"
        elif any(word in text for word in ['中等', 'medium', 'moderate', '普通']):
            return "中等"
        elif any(word in text for word in ['困难', 'hard', 'difficult', '复杂']):
            return "困难"

        return None

    @staticmethod
    def deduplicate(recipes: List[RecipeModel]) -> List[RecipeModel]:
        """
        去重菜谱列表(基于名称)

        Args:
            recipes: 菜谱列表

        Returns:
            去重后的菜谱列表
        """
        seen = set()
        unique_recipes = []

        for recipe in recipes:
            # 使用标准化的名称作为去重键
            name_key = re.sub(r'\s+', '', recipe.name.lower())

            if name_key not in seen:
                seen.add(name_key)
                unique_recipes.append(recipe)

        logger.info(f"Deduplicated: {len(recipes)} -> {len(unique_recipes)} recipes")
        return unique_recipes

    @staticmethod
    def merge_recipes(recipe1: RecipeModel, recipe2: RecipeModel) -> RecipeModel:
        """
        合并两个菜谱(当名称相同但数据来源不同时)

        Args:
            recipe1: 菜谱1
            recipe2: 菜谱2

        Returns:
            合并后的菜谱
        """
        merged_data = recipe1.dict()

        # 合并策略: 优先使用更完整的数据
        for key, value2 in recipe2.dict().items():
            value1 = merged_data.get(key)

            # 如果字段1为空,使用字段2
            if not value1 and value2:
                merged_data[key] = value2

            # 对于列表,合并并去重
            elif isinstance(value1, list) and isinstance(value2, list):
                combined = value1 + value2
                # 简单去重
                merged_data[key] = list(dict.fromkeys(combined))

            # 对于字典,合并键值对
            elif isinstance(value1, dict) and isinstance(value2, dict):
                merged_data[key] = {**value1, **value2}

        return RecipeModel(**merged_data)
