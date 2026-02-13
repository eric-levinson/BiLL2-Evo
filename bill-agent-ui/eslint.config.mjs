import { dirname } from 'path'
import { fileURLToPath } from 'url'
import { FlatCompat } from '@eslint/eslintrc'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const compat = new FlatCompat({
  baseDirectory: __dirname
})

const eslintConfig = [
  ...compat.extends('next/core-web-vitals', 'next/typescript'),

  // Architectural boundary: @/lib/ cannot import from upper layers
  {
    files: ['src/lib/**/*.ts', 'src/lib/**/*.tsx'],
    // Exclude composition files that intentionally wire across boundaries
    ignores: ['src/lib/ai/tools/**'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              group: ['@/hooks', '@/hooks/*'],
              message:
                'ARCHITECTURAL VIOLATION: lib/ cannot import from hooks/. Move the hook dependency into the component layer, or extract the shared logic into a new lib/ utility. See docs/bill-agent-ui/layers.md'
            },
            {
              group: ['@/components', '@/components/*'],
              message:
                'ARCHITECTURAL VIOLATION: lib/ cannot import from components/. Move the shared type to @/types/ or extract shared logic into lib/. See docs/bill-agent-ui/layers.md'
            },
            {
              group: ['@/app', '@/app/*'],
              message:
                'ARCHITECTURAL VIOLATION: lib/ cannot import from app/. The app layer depends on lib, not the other way around. See docs/bill-agent-ui/layers.md'
            }
          ]
        }
      ]
    }
  },

  // Architectural boundary: @/hooks/ cannot import from upper layers
  {
    files: ['src/hooks/**/*.ts', 'src/hooks/**/*.tsx'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              group: ['@/components', '@/components/*'],
              message:
                'ARCHITECTURAL VIOLATION: hooks/ cannot import from components/. Hooks should only depend on lib/ and types/. See docs/bill-agent-ui/layers.md'
            },
            {
              group: ['@/app', '@/app/*'],
              message:
                'ARCHITECTURAL VIOLATION: hooks/ cannot import from app/. See docs/bill-agent-ui/layers.md'
            }
          ]
        }
      ]
    }
  },

  // Architectural boundary: @/types/ cannot import from any internal module
  {
    files: ['src/types/**/*.ts', 'src/types/**/*.tsx'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              group: [
                '@/lib',
                '@/lib/*',
                '@/hooks',
                '@/hooks/*',
                '@/components',
                '@/components/*',
                '@/app',
                '@/app/*'
              ],
              message:
                'ARCHITECTURAL VIOLATION: types/ must be dependency-free — it cannot import from any internal module. See docs/bill-agent-ui/layers.md'
            }
          ]
        }
      ]
    }
  }
]

export default eslintConfig
