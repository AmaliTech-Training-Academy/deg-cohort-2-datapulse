export type ApiRuleType = 'null_check' | 'type_check' | 'range_check' | 'uniqueness_check';

export interface RuleBatchItem {
  column_name: string;
  rule_type: ApiRuleType;
  rule_config: Record<string, unknown>;
}

export type RulesBatchRequest = RuleBatchItem[];

export interface CreatedRuleItem {
  id: string;
  dataset: string;
  column_name: string;
  rule_type: string;
  rule_config: Record<string, unknown>;
  created_at: string;
}

export interface SkippedRuleItem {
  index: number;
  column_name: string;
  rule_type: string;
  reason: string;
}

export interface RuleBatchErrorItem {
  index: number;
  column_name: string;
  rule_type: string;
  detail: Record<string, string[]>;
}

export interface RulesBatchResponse {
  created: CreatedRuleItem[];
  skipped: SkippedRuleItem[];
  errors: RuleBatchErrorItem[];
  summary: {
    total: number;
    created: number;
    skipped: number;
    errors: number;
  };
}
