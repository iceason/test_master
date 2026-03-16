import argparse
import json
import yaml
import logging
from collections import Counter, defaultdict
from typing import Dict, Any, Set, Optional, List
from field_generators import TestCaseGenerator, DatasetGenerator, SchemaValidator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Auto-generate test cases or datasets from YAML/JSON Schema (OpenAPI 3.0 compatible)")
    parser.add_argument("-i", "--input", required=True, help="Input YAML/JSON schema file")
    parser.add_argument("-o", "--output", required=True, help="Output JSON file")
    parser.add_argument("--api-name", required=True, help="API name prefix (e.g., USER_CREATE)")
    parser.add_argument("--mode", choices=["test_cases", "dataset"], default="test_cases", help="Generation mode")
    parser.add_argument("--count", type=int, default=10, help="Number of records for dataset mode (max: 1000)")
    parser.add_argument("--disable-categories", nargs="+", choices=["Positive", "Negative", "Boundary", "Security"],
                        help="Disable specific test case categories")
    parser.add_argument("--schema-type", default="openapi", choices=["openapi", "custom"],
                        help="Schema type (OpenAPI 3.0 or custom)")
    args = parser.parse_args()

    # 校验参数
    args.count = min(args.count, 1000)  # 限制最大生成数量
    disabled_categories = set(args.disable_categories or [])

    # 加载Schema
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            if args.input.endswith(".yaml") or args.input.endswith(".yml"):
                schema = yaml.safe_load(f)
            else:
                schema = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load schema file: {e}")
        return

    # 验证Schema合法性
    validator = SchemaValidator(schema_type=args.schema_type)
    if not validator.validate(schema):
        logger.error("Schema validation failed, exit generation")
        return

    # 生成逻辑
    if args.mode == "dataset":
        logger.info(f"🚀 Generating dataset with {args.count} records (schema type: {args.schema_type})...")
        generator = DatasetGenerator()
        try:
            dataset = generator.generate_dataset(schema, args.count)
        except Exception as e:
            logger.error(f"Dataset generation failed: {e}")
            return

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Generated {len(dataset)} records to {args.output}")

    else:
        logger.info("🚀 Generating comprehensive test cases...")
        generator = TestCaseGenerator(disabled_categories=disabled_categories)
        dataset_generator = DatasetGenerator()
        
        try:
            all_cases = generator.generate_all_cases(schema, args.api_name)
            
            # Enrich test cases with full payload
            # Generate a base valid record using DatasetGenerator
            base_record = dataset_generator.generate_record(schema)
            
            for case in all_cases:
                # Create a copy of the base record to modify
                full_payload = json.loads(json.dumps(base_record))
                
                # Update the target field with the specific test input value
                target_field = case.get("target_field")
                input_value = case.get("input_value")
                
                if target_field:
                    # Handle nested fields (e.g., "address.city") and array fields (e.g., "items[*].id")
                    parts = target_field.replace("[*]", "").split(".")
                    current = full_payload
                    
                    try:
                        for i, part in enumerate(parts[:-1]):
                            if part not in current:
                                # Create nested structure if missing (though base_record should have it)
                                current[part] = {}
                            current = current[part]
                            
                            # If we encounter a list but expect a dict (due to array handling), take first item
                            if isinstance(current, list) and len(current) > 0:
                                current = current[0]
                        
                        # Set the value on the leaf node
                        leaf_key = parts[-1]
                        if isinstance(current, dict):
                            current[leaf_key] = input_value
                        elif isinstance(current, list) and len(current) > 0:
                            # Edge case: if the leaf is part of a list
                             # This logic is simplified; for array items, we might need more complex handling
                            pass
                            
                        # Update input_value in the case object to be the full payload
                        case["input_value"] = full_payload
                        
                    except Exception as e:
                        logger.warning(f"Failed to inject input value for field {target_field}: {e}")
                        # Fallback: keep original input_value if injection fails
            
        except Exception as e:
            logger.error(f"Test case generation failed: {e}")
            return

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(all_cases, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Generated {len(all_cases)} test cases to {args.output}")
        analyze_coverage(all_cases, schema, disabled_categories)


def analyze_coverage(cases: list, schema: Dict[str, Any], disabled_categories: Set[str]):
    """Enhanced coverage analysis with more dimensions"""
    logger.info("\n📊 === Test Case Coverage Analysis ===")

    total_cases = len(cases)
    logger.info(f"Total Cases: {total_cases}")
    if total_cases == 0:
        logger.warning("No test cases generated")
        return

    # 1. Category Analysis (exclude disabled)
    category_counts = Counter(c["test_type"] for c in cases if "test_type" in c)
    logger.info("\n--- By Category ---")
    expected_categories = {c.lower() for c in ({"Positive", "Negative", "Boundary", "Security"} - disabled_categories)}
    for cat in sorted(expected_categories):
        count = category_counts.get(cat, 0)
        percentage = (count / total_cases) * 100
        logger.info(f"  - {cat}: {count} ({percentage:.1f}%)")

    # Check missing enabled categories
    missing_cats = expected_categories - set(category_counts.keys())
    if missing_cats:
        logger.warning(f"⚠️  Missing enabled categories: {missing_cats}")

    # 2. Field Analysis (support nested fields)
    logger.info("\n--- By Field ---")
    field_paths = get_all_field_paths(schema)
    field_counts = Counter(c["target_field"] for c in cases)

    for field_path in sorted(field_paths):
        count = field_counts.get(field_path, 0)
        logger.info(f"  - {field_path}: {count}")
        if count == 0:
            logger.warning(f"⚠️  No test cases generated for field '{field_path}'")

    # 3. Type Coverage
    logger.info("\n--- By Field Type ---")
    type_counter = Counter()
    for case in cases:
        field = case["target_field"]
        field_type = get_field_type(schema, field)
        if field_type:
            type_counter[field_type] += 1

    for field_type, count in type_counter.most_common():
        percentage = (count / total_cases) * 100
        logger.info(f"  - {field_type}: {count} ({percentage:.1f}%)")

    logger.info("\n=======================================\n")


def get_all_field_paths(schema: Dict[str, Any], parent_path: str = "") -> Set[str]:
    """Recursively get all field paths (supports nested objects/arrays)"""
    field_paths = set()
    properties = schema.get("properties", schema)  # 兼容OpenAPI和自定义Schema

    for field, config in properties.items():
        full_path = f"{parent_path}.{field}" if parent_path else field

        # 处理嵌套对象
        if config.get("type") == "object" and "properties" in config:
            field_paths.update(get_all_field_paths(config, full_path))
        # 处理数组项
        elif config.get("type") == "array" and "items" in config:
            item_config = config["items"]
            if item_config.get("type") == "object" and "properties" in item_config:
                field_paths.update(get_all_field_paths(item_config, f"{full_path}[*]"))
            else:
                field_paths.add(full_path)
        else:
            field_paths.add(full_path)

    return field_paths


def get_field_type(schema: Dict[str, Any], field_path: str) -> Optional[str]:
    """Get type of a field by path (supports nested)"""
    parts = field_path.split(".")
    current = schema.get("properties", schema)

    for part in parts:
        # 处理数组下标 [*]
        clean_part = part.replace("[*]", "")
        if clean_part not in current:
            return None

        current = current[clean_part]
        # 数组项类型
        if "[*]" in part and current.get("type") == "array" and "items" in current:
            current = current["items"]

    return current.get("type")


if __name__ == "__main__":
    main()