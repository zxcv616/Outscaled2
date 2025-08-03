// Mock axios for testing - ES module compatible
const mockAxios = {
  create: jest.fn(() => mockAxios),
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  patch: jest.fn(),
  interceptors: {
    request: { use: jest.fn(), eject: jest.fn() },
    response: { use: jest.fn(), eject: jest.fn() }
  },
  defaults: {
    baseURL: 'http://localhost:8000',
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json'
    }
  }
};

// Support both CommonJS and ES module imports
module.exports = mockAxios;
module.exports.default = mockAxios; 