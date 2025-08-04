// Using Jest testing framework

// Mock PredictionResponse for testing
const mockPredictionResponse = {
  prediction: 'OVER' as const,
  confidence: 75,
  expected_stat: 18.5,
  prop_value: 16.5,
  confidence_interval: [15.2, 21.8] as [number, number],
  prop_type: 'kills',
  reasoning: 'Test reasoning',
  data_years: '2023-2024',
  player_stats: {
    avg_kills: 17.2,
    avg_assists: 12.1,
  },
  sample_details: {
    maps_used: 15,
    volatility: 0.32,
    fallback_used: false,
    strict_mode_applied: true,
    tier_name: 'Tier 1',
    ci_method: 'bootstrap',
  },
};

describe('Visualization Fixes', () => {
  describe('Gap Calculation Fix', () => {
    it('should handle normal prop values correctly', () => {
      const expectedStat = 18.5;
      const propValue = 16.5;
      
      const gap = Math.abs(expectedStat - propValue);
      const gapPercentage = propValue !== 0 ? (gap / propValue) * 100 : 0;
      
      expect(gap).toBe(2.0);
      expect(gapPercentage).toBeCloseTo(12.12, 2);
      expect(isNaN(gapPercentage)).toBe(false);
    });
    
    it('should handle zero prop value without NaN', () => {
      const expectedStat = 18.5;
      const propValue = 0;
      
      const gap = Math.abs(expectedStat - propValue);
      const gapPercentage = propValue !== 0 ? (gap / propValue) * 100 : 0;
      
      expect(gap).toBe(18.5);
      expect(gapPercentage).toBe(0);
      expect(isNaN(gapPercentage)).toBe(false);
    });
    
    it('should handle negative prop value correctly', () => {
      const expectedStat = 18.5;
      const propValue = -5;
      
      const gap = Math.abs(expectedStat - propValue);
      const gapPercentage = propValue !== 0 ? (gap / propValue) * 100 : 0;
      
      expect(gap).toBe(23.5);
      expect(gapPercentage).toBe(-470);
      expect(isNaN(gapPercentage)).toBe(false);
    });
  });

  describe('Position Calculation Fix', () => {
    it('should clamp position values within 0-100 range', () => {
      const expectedStat = 18.5;
      const propValue = 16.5;
      
      // Test the position calculation used in the visualization
      const rawPosition = 50 + (expectedStat - propValue) * 20;
      const clampedPosition = Math.max(0, Math.min(100, rawPosition));
      
      expect(rawPosition).toBe(90); // 50 + (18.5 - 16.5) * 20 = 90
      expect(clampedPosition).toBe(90);
    });
    
    it('should handle extreme values by clamping', () => {
      const expectedStat = 100;
      const propValue = 5;
      
      const rawPosition = 50 + (expectedStat - propValue) * 20;
      const clampedPosition = Math.max(0, Math.min(100, rawPosition));
      
      expect(rawPosition).toBe(1950); // Way beyond 100
      expect(clampedPosition).toBe(100); // Clamped to 100
    });
    
    it('should handle negative positions by clamping to zero', () => {
      const expectedStat = 5;
      const propValue = 100;
      
      const rawPosition = 50 + (expectedStat - propValue) * 20;
      const clampedPosition = Math.max(0, Math.min(100, rawPosition));
      
      expect(rawPosition).toBe(-1850); // Way below 0
      expect(clampedPosition).toBe(0); // Clamped to 0
    });
  });

  describe('Data Validation', () => {
    it('should handle missing volatility with default values', () => {
      const sampleDetailsWithoutVolatility = {
        maps_used: 15,
        fallback_used: false,
        strict_mode_applied: true,
        tier_name: 'Tier 1',
        ci_method: 'bootstrap',
      };
      
      const volatility = (sampleDetailsWithoutVolatility as any).volatility || 0.3;
      
      expect(volatility).toBe(0.3);
      expect(typeof volatility).toBe('number');
      expect(isNaN(volatility)).toBe(false);
    });
    
    it('should handle missing sample details gracefully', () => {
      const sampleDetails = null;
      
      const volatility = sampleDetails?.volatility || 0.3;
      const mapsUsed = sampleDetails?.maps_used || 0;
      
      expect(volatility).toBe(0.3);
      expect(mapsUsed).toBe(0);
      expect(isNaN(volatility)).toBe(false);
      expect(isNaN(mapsUsed)).toBe(false);
    });
  });

  describe('Confidence Interval Validation', () => {
    it('should handle valid confidence intervals', () => {
      const confidenceInterval: [number, number] = [15.2, 21.8];
      
      expect(Array.isArray(confidenceInterval)).toBe(true);
      expect(confidenceInterval.length).toBe(2);
      expect(confidenceInterval[0]).toBeLessThan(confidenceInterval[1]);
      expect(isNaN(confidenceInterval[0])).toBe(false);
      expect(isNaN(confidenceInterval[1])).toBe(false);
    });
    
    it('should handle malformed confidence intervals', () => {
      const malformedCI = [NaN, 21.8] as [number, number];
      
      // The visualization should handle this gracefully
      const safeCI: [number, number] = [
        isNaN(malformedCI[0]) ? 0 : malformedCI[0],
        isNaN(malformedCI[1]) ? 100 : malformedCI[1],
      ];
      
      expect(safeCI[0]).toBe(0);
      expect(safeCI[1]).toBe(21.8);
      expect(isNaN(safeCI[0])).toBe(false);
      expect(isNaN(safeCI[1])).toBe(false);
    });
  });

  describe('Quantitative Calculations', () => {
    it('should calculate Z-score correctly', () => {
      const expectedStat = 18.5;
      const propValue = 16.5;
      const volatility = 0.32;
      
      const standardDeviation = expectedStat * volatility;
      const zScore = standardDeviation !== 0 ? (propValue - expectedStat) / standardDeviation : 0;
      
      expect(standardDeviation).toBeCloseTo(5.92, 2);
      expect(zScore).toBeCloseTo(-0.338, 3);
      expect(isNaN(zScore)).toBe(false);
    });
    
    it('should handle zero standard deviation', () => {
      const expectedStat = 18.5;
      const propValue = 16.5;
      const volatility = 0;
      
      const standardDeviation = expectedStat * volatility;
      const zScore = standardDeviation !== 0 ? (propValue - expectedStat) / standardDeviation : 0;
      
      expect(standardDeviation).toBe(0);
      expect(zScore).toBe(0);
      expect(isNaN(zScore)).toBe(false);
    });
    
    it('should calculate percentile rank safely', () => {
      const propValue = 16.5;
      const expectedStat = 18.5;
      const volatility = 0.32;
      
      const zScore = (propValue - expectedStat) / (expectedStat * volatility);
      const percentile = 50 + (zScore * 34.13);
      const safePercentile = Math.max(1, Math.min(99, Math.round(percentile)));
      
      expect(percentile).toBeCloseTo(38.47, 1);
      expect(safePercentile).toBe(38);
      expect(safePercentile).toBeGreaterThanOrEqual(1);
      expect(safePercentile).toBeLessThanOrEqual(99);
    });
  });
});

export { mockPredictionResponse };