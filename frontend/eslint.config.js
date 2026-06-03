const eslint = require('@eslint/js');
const tseslint = require('typescript-eslint');
const angular = require('angular-eslint');
const prettierConfig = require('eslint-config-prettier');

module.exports = tseslint.config(
  {
    ignores: [
      'dist/**',
      '.angular/**',
      'coverage/**',
      'out-tsc/**',
      'node_modules/**',
      'playwright-report/**',
      'test-results/**',
    ],
  },

  // TypeScript source files
  {
    files: ['**/*.ts'],
    extends: [
      eslint.configs.recommended,
      ...tseslint.configs.recommended,
      ...tseslint.configs.stylistic,
      ...angular.configs.tsRecommended,
    ],
    processor: angular.processInlineTemplates,
    rules: {
      '@angular-eslint/directive-selector': [
        'error',
        { type: 'attribute', prefix: 'app', style: 'camelCase' },
      ],
      '@angular-eslint/component-selector': [
        'error',
        { type: 'element', prefix: 'app', style: 'kebab-case' },
      ],
      // Codebase uses form.getRawValue() non-null assertions (email!, password!)
      '@typescript-eslint/no-non-null-assertion': 'off',
      // Allow * as AuthActions namespace imports (NgRx pattern)
      '@typescript-eslint/no-namespace': 'off',
      // Allow _ prefix for intentionally unused params
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
      // CVA components declare empty onChange/onTouched arrow stubs that Angular replaces at runtime
      '@typescript-eslint/no-empty-function': ['error', { allow: ['arrowFunctions'] }],
      // CVA components require constructor injection (@Optional @Self NgControl) — inject() cannot replace this
      '@angular-eslint/prefer-inject': 'off',
    },
  },

  // Test files — relaxed rules
  {
    files: ['**/*.spec.ts'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },

  // HTML templates
  {
    files: ['**/*.html'],
    extends: [...angular.configs.templateRecommended, ...angular.configs.templateAccessibility],
    rules: {
      // Start as warnings; fix HTML templates incrementally
      '@angular-eslint/template/interactive-supports-focus': 'warn',
      '@angular-eslint/template/click-events-have-key-events': 'warn',
    },
  },

  // Prettier MUST be last — disables all formatting-conflicting rules
  prettierConfig,
);
