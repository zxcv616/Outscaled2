module.exports = {
  // Automatically clear mock calls and instances between every test
  clearMocks: true,
  
  // Indicates whether the coverage information should be collected while executing the test
  collectCoverage: true,
  
  // An array of glob patterns indicating a set of files for which coverage information should be collected
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.tsx',
    '!src/reportWebVitals.ts',
    '!src/setupTests.ts'
  ],
  
  // The directory where Jest should output its coverage files
  coverageDirectory: 'coverage',
  
  // An array of file extensions your modules use
  moduleFileExtensions: ['js', 'json', 'jsx', 'ts', 'tsx', 'node'],
  
  // A map from regular expressions to module names that allow to stub out resources with a single module
  moduleNameMapper: {
    // Handle CSS imports (with CSS modules)
    '^.+\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    
    // Handle image imports
    '^.+\\.(jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$': '<rootDir>/__mocks__/fileMock.js',
    
    // Handle style imports
    '^.+\\.(css|less|scss|sass)$': '<rootDir>/__mocks__/styleMock.js',
    
    // Handle ES module imports - mock axios completely
    '^axios$': '<rootDir>/__mocks__/axiosMock.js'
  },
  
  // Setup files
  setupFilesAfterEnv: [
    '<rootDir>/src/setupTests.ts',
    '<rootDir>/__mocks__/setupAxiosMock.js'
  ],
  
  // The test environment that will be used for testing
  testEnvironment: 'jsdom',
  
  // The glob patterns Jest uses to detect test files
  testMatch: [
    '**/__tests__/**/*.(js|jsx|ts|tsx)',
    '**/*.(test|spec).(js|jsx|ts|tsx)'
  ],
  
  // An array of regexp pattern strings that are matched against all test paths, matched tests are skipped
  testPathIgnorePatterns: [
    '/node_modules/',
    '/dist/',
    '/build/'
  ],
  
  // The regexp pattern or array of patterns that Jest uses to detect test files
  testRegex: '(/__tests__/.*|(\\.|/)(test|spec))\\.(jsx?|tsx?)$',
  
  // This option allows the use of a custom results processor
  testResultsProcessor: 'jest-sonar-reporter',
  
  // Indicates whether each individual test should be reported during the run
  verbose: true,
  
  // Transform configuration for handling ES modules
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest',
    '^.+\\.(js|jsx)$': 'babel-jest'
  },
  
  // Global setup for ES modules
  globals: {
    'ts-jest': {
      useESM: false,
    },
  },
}; 