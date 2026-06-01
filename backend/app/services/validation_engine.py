import json
import pandas as pd


class ValidationEngine:

    def run_all_checks(self, df: pd.DataFrame, rules: list) -> list:
        results = []
        for rule in rules:
            params = json.loads(rule.parameters) if rule.parameters else {}
            if rule.rule_type == "NOT_NULL":
                result = self.null_check(df, rule.field_name)
            elif rule.rule_type == "DATA_TYPE":
                result = self.type_check(df, rule.field_name, params.get("expected_type", "str"))
            elif rule.rule_type == "RANGE":
                result = self.range_check(
                    df, rule.field_name, params.get("min"), params.get("max")
                )
            elif rule.rule_type == "UNIQUE":
                result = self.unique_check(df, rule.field_name)
            elif rule.rule_type == "REGEX":
                result = self.regex_check(df, rule.field_name, params.get("pattern", ""))
            else:
                result = {
                    "passed": False,
                    "failed_rows": 0,
                    "total_rows": len(df),
                    "details": f"Unknown rule_type: {rule.rule_type}",
                }
            result["rule_id"] = rule.id
            results.append(result)
        return results

    def null_check(self, df: pd.DataFrame, field: str) -> dict:
        if field not in df.columns:
            return {
                "passed": False,
                "failed_rows": len(df),
                "total_rows": len(df),
                "details": f"Field {field} not found in dataset",
            }
        null_count = int(df[field].isnull().sum())
        return {
            "passed": null_count == 0,
            "failed_rows": null_count,
            "total_rows": len(df),
            "details": f"{null_count} null values found in {field}",
        }

    def type_check(self, df, field, expected_type):
        """
        TODO: Check data types.

        Steps:
        1. Verify field exists in df
        2. Check if values can be cast to expected_type
        3. Count rows that fail the type check
        4. Return result dict with passed/failed_rows/details
        """
        return {
            "passed": False,
            "failed_rows": 0,
            "total_rows": len(df),
            "details": "type_check not yet implemented",
        }

    def range_check(self, df, field, min_val, max_val):
        """
        TODO: Check value ranges.

        Steps:
        1. Verify field exists and is numeric
        2. Count rows where value < min_val or value > max_val
        3. Return result dict
        """
        return {
            "passed": False,
            "failed_rows": 0,
            "total_rows": len(df),
            "details": "range_check not yet implemented",
        }

    def unique_check(self, df, field):
        """
        TODO: Check uniqueness.

        Steps:
        1. Verify field exists
        2. Count duplicate values
        3. Return result dict
        """
        return {
            "passed": False,
            "failed_rows": 0,
            "total_rows": len(df),
            "details": "unique_check not yet implemented",
        }

    def regex_check(self, df, field, pattern):
        """
        TODO: Check regex pattern matching.

        Steps:
        1. Verify field exists
        2. Apply regex pattern to each non-null value
        3. Count rows that do not match
        4. Return result dict
        """
        return {
            "passed": False,
            "failed_rows": 0,
            "total_rows": len(df),
            "details": "regex_check not yet implemented",
        }
