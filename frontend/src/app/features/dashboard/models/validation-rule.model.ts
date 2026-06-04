import { ApiRuleType } from './rules-batch.model';
import { ValidationRule } from '../../../shared/models/dashboard.models';

export interface ApiValidationRule {
  id: string;
  dataset: string;
  column_name: string;
  rule_type: ApiRuleType;
  rule_config: Record<string, unknown>;
  created_at: string;
  last_failing_rows: number | null;
  last_passing_rows: number | null;
  average_score: number | null;
}

export interface ApiRulesListResponse {
  total_failing_rows: number;
  total_passing_rows: number;
  rule_type_scores: {
    null_check: number | null;
    type_check: number | null;
    range_check: number | null;
    uniqueness_check: number | null;
  };
  count: number;
  next: string | null;
  previous: string | null;
  results: ApiValidationRule[];
}

export interface CreateRuleRequest {
  column_name: string;
  rule_type: ApiRuleType;
  rule_config: Record<string, unknown>;
}

// ── Mapping helpers ──────────────────────────────────────────────────────────

export function mapFrontendTypeToApi(type: string): ApiRuleType {
  switch (type) {
    case 'not_null':
      return 'null_check';
    case 'type_check':
      return 'type_check';
    case 'range':
      return 'range_check';
    case 'unique':
      return 'uniqueness_check';
    default:
      return 'null_check';
  }
}

export function buildRuleConfig(type: string, params: string): Record<string, unknown> {
  if (type === 'type_check') {
    const expectedType = params.trim().split(/[\s,]/)[0] || 'string';
    return { expected_type: expectedType };
  }
  if (type === 'range') {
    const minMatch = /min[=:\s]+(-?[\d.]+)/i.exec(params);
    const maxMatch = /max[=:\s]+(-?[\d.]+)/i.exec(params);
    return {
      min: minMatch ? parseFloat(minMatch[1]) : 0,
      max: maxMatch ? parseFloat(maxMatch[1]) : 100,
    };
  }
  return {};
}

function mapApiRuleType(apiType: ApiRuleType): ValidationRule['type'] {
  switch (apiType) {
    case 'null_check':
      return 'not_null';
    case 'type_check':
      return 'type_check';
    case 'range_check':
      return 'range';
    case 'uniqueness_check':
      return 'unique';
    default:
      return 'not_null';
  }
}

function buildRuleName(apiType: ApiRuleType, column: string): string {
  switch (apiType) {
    case 'null_check':
      return `No null ${column}`;
    case 'type_check':
      return `Type: ${column}`;
    case 'range_check':
      return `${column} range`;
    case 'uniqueness_check':
      return `Unique ${column}`;
  }
}

function buildRuleDescription(
  apiType: ApiRuleType,
  column: string,
  config: Record<string, unknown>,
): string {
  switch (apiType) {
    case 'null_check':
      return `Flag any missing values in ${column}`;
    case 'type_check':
      return `Values must match type: ${config['expected_type'] ?? 'string'}`;
    case 'range_check':
      return `Values must be between ${config['min']} and ${config['max']}`;
    case 'uniqueness_check':
      return `No duplicate values allowed in ${column}`;
  }
}

export function mapApiRule(api: ApiValidationRule): ValidationRule {
  const failing = api.last_failing_rows ?? 0;
  return {
    id: api.id,
    name: buildRuleName(api.rule_type, api.column_name),
    description: buildRuleDescription(api.rule_type, api.column_name, api.rule_config),
    type: mapApiRuleType(api.rule_type),
    column: api.column_name,
    enabled: true,
    status: failing > 0 ? 'failing' : 'passing',
    failingRows: failing > 0 ? failing : undefined,
  };
}
