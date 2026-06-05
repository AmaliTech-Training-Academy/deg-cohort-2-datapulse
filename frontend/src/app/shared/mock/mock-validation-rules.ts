import { ValidationRule } from '../models/dashboard.models';

export const MOCK_VALIDATION_RULES: Record<string, ValidationRule[]> = {
  d1: [
    { id: 'r1', name: 'No null emails', description: 'email column must not contain null values', type: 'not_null', column: 'email', enabled: true, status: 'failing', failingRows: 318 },
    { id: 'r2', name: 'Type: signup_date', description: 'must be a valid ISO 8601 date', type: 'type_check', column: 'signup_date', enabled: true, status: 'failing', failingRows: 12 },
    { id: 'r3', name: 'Age range 18–120', description: 'age must fall within bounds', type: 'range', column: 'age', enabled: true, status: 'passing' },
    { id: 'r4', name: 'Unique customer_id', description: 'customer_id must be unique across rows', type: 'unique', column: 'customer_id', enabled: true, status: 'failing', failingRows: 5 },
    { id: 'r5', name: 'Phone format (E.164)', description: 'deprecated — replaced by libphonenumber check', type: 'format', column: 'phone', enabled: false, status: 'passing', deprecated: true },
  ],
  d2: [
    { id: 'r6', name: 'No null account IDs', description: 'account_id must not be null', type: 'not_null', column: 'account_id', enabled: true, status: 'passing' },
    { id: 'r7', name: 'Positive balance', description: 'balance must be >= 0', type: 'range', column: 'balance', enabled: true, status: 'passing' },
    { id: 'r8', name: 'Unique account_id', description: 'account_id must be unique across rows', type: 'unique', column: 'account_id', enabled: true, status: 'passing' },
  ],
  d3: [
    { id: 'r9', name: 'No null emails', description: 'email column must not contain null values', type: 'not_null', column: 'email', enabled: true, status: 'failing', failingRows: 240 },
    { id: 'r10', name: 'Valid phone format', description: 'phone must match E.164 format', type: 'format', column: 'phone', enabled: true, status: 'failing', failingRows: 1000 },
  ],
  d4: [
    { id: 'r11', name: 'Type: transaction_date', description: 'must be a valid ISO 8601 date', type: 'type_check', column: 'transaction_date', enabled: true, status: 'passing' },
    { id: 'r12', name: 'Positive amount', description: 'amount must be greater than zero', type: 'range', column: 'amount', enabled: true, status: 'passing' },
  ],
};

export const MOCK_DATASET_COLUMNS: Record<string, string[]> = {
  d1: ['email', 'signup_date', 'age', 'customer_id', 'phone', 'name', 'country'],
  d2: ['account_id', 'balance', 'currency', 'status', 'created_at'],
  d3: ['contact_id', 'email', 'phone', 'name', 'created_at'],
  d4: ['transaction_id', 'transaction_date', 'amount', 'status', 'account_id'],
};
