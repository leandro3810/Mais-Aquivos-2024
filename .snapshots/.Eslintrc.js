module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  extends: [
    'eslint:recommended',
    'plugin:react/recommended', // Use com projetos React, remova se não for necessário
    'plugin:@typescript-eslint/recommended', // Use com TypeScript, remova se não for necessário
    'prettier', // Integração com Prettier, remova se não usar Prettier
  ],
  parser: '@typescript-eslint/parser', // Utilize com TypeScript, remova se usar apenas JavaScript
  parserOptions: {
    ecmaVersion: 12,
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true, // Use com projetos React, remova se não for necessário
    },
  },
  plugins: [
    'react', // Use com React, remova se não for necessário
    '@typescript-eslint', // Use com TypeScript, remova se não for necessário
  ],
  rules: {
    'no-unused-vars': 'warn', // Alerta para variáveis não utilizadas
    'no-console': 'warn', // Alerta para uso de console.log
    'react/prop-types': 'off', // Desativa validação de propTypes (se usar TypeScript)
    '@typescript-eslint/no-unused-vars': ['warn'], // Configuração para TypeScript
  },
  settings: {
    react: {
      version: 'detect', // Detecta a versão do React automaticamente
    },
  },
};
