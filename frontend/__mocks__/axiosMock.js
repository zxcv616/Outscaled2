// Mock axios for testing
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

module.exports = mockAxios; 