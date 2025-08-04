# Quantitative Analysis Components

Professional-grade components for quantitative analysts working with sports betting predictions.

## Components Overview

### 1. DeviationMetrics
**Purpose**: Statistical deviation analysis with Z-scores, percentiles, and variance ratios

**Features**:
- Z-score calculations for statistical significance
- Percentile rankings
- Deviation ratios (relative to prop value)
- Volatility index measurements
- Automated interpretation of statistical significance

**Key Metrics**:
- Expected vs Line deviation
- Deviation ratio (percentage)
- Volatility index
- Statistical summary with extreme deviation warnings

### 2. VolatilityRiskClassification
**Purpose**: Risk assessment with volatility scoring and management recommendations

**Features**:
- Comprehensive volatility scoring (0-100)
- Risk level classification (Very Low to Very High)
- Component risk breakdowns:
  - Confidence Stability
  - Data Quality Risk
  - Model Uncertainty
- Tailored risk management recommendations

**Risk Levels**:
- Very Low (0-20): Highly stable predictions
- Low (21-35): Stable with acceptable variance
- Medium (36-55): Moderate uncertainty
- High (56-75): Elevated uncertainty
- Very High (76-100): Extreme uncertainty

### 3. SensitivityCurve
**Purpose**: Interactive sensitivity analysis showing prediction response to prop changes

**Features**:
- Dynamic sensitivity curve visualization
- Probability distribution across prop values
- Key sensitivity points identification:
  - Current sensitivity at prop line
  - 50/50 transition point
  - Peak sensitivity point
  - Over probability at current prop
- Interactive tooltips with detailed metrics

**Visualizations**:
- Probability curve (0-100%)
- Sensitivity curve (rate of change)
- Reference lines for current prop and 50% probability
- Highlighted current point

### 4. ContextualDataSnapshot
**Purpose**: Comprehensive contextual information about data sources and quality

**Features**:
- Four context categories:
  - **Temporal**: Data period, recency, seasonality
  - **Sample**: Size, coverage, representation
  - **Environmental**: Tournament, opponent, conditions
  - **Methodological**: Data tier, CI method, filtering
- Contextual risk assessment
- Sample sources breakdown with percentages
- Expandable detailed view

### 5. DataIntegrityFlags
**Purpose**: Data quality flags and warnings with impact assessments

**Features**:
- Multi-category flag system:
  - Data Quality
  - Methodology
  - Sample Size
  - Temporal
  - Model
- Severity levels: Critical, High, Medium, Low
- Impact assessments and recommendations
- Overall integrity scoring
- Flag summaries by category

**Flag Types**:
- Critical: Critically low sample size
- High: Low sample size, low data tier
- Medium: Fallback data, high volatility
- Info: Historical data, wide confidence intervals
- Success: Good data integrity confirmation

### 6. RecommendationBadges
**Purpose**: AI-generated betting recommendations with confidence tiers

**Features**:
- Overall recommendation scoring (1-5 scale)
- Four recommendation categories:
  - **Bet Recommendation**: STRONG BUY, BUY, SMALL BET, AVOID BET
  - **Risk Level**: LOW, MEDIUM, HIGH RISK
  - **Value Assessment**: EXCELLENT, GOOD, FAIR, POOR VALUE  
  - **Confidence Tier**: TIER A, B, C, D
- Detailed reasoning for each recommendation
- Quick action guide with position sizing suggestions

**Recommendation Logic**:
- Combines confidence, edge percentage, and sample size
- Factors in data quality and uncertainty
- Provides specific position sizing guidance

### 7. ExpandableMetadata
**Purpose**: Detailed technical metadata and debugging information

**Features**:
- Six metadata sections:
  - Request Parameters
  - Raw Model Output
  - Player Analytics
  - Sample Metadata
  - Prediction Curve Data (technical)
  - Technical Specifications (technical)
- Technical/Standard view toggle
- Copy functionality for each section
- Smart data rendering:
  - Tables for array data
  - Nested lists for objects
  - Formatted chips for simple arrays

## Enhanced Prediction Result Integration

### Quant Mode Toggle
- **Standard Mode**: Traditional view with reasoning and basic metrics
- **Quantitative Mode**: Advanced analysis with all quantitative components
- Smooth transition between modes
- Mode-specific loading states

### Tabbed Interface (Quant Mode)
1. **Deviation Analysis**: Statistical deviation metrics
2. **Risk Assessment**: Volatility and risk classification
3. **Sensitivity Curve**: Interactive sensitivity analysis
4. **Data Context**: Contextual data snapshot
5. **Raw Metadata**: Technical debugging info (advanced view)

### Always Visible (Quant Mode)
- AI Recommendations (badges)
- Data Integrity Flags
- Enhanced core metrics with confidence intervals and edges

## Technical Implementation

### Architecture
- **Component-based**: Each analysis type is a separate component
- **Type-safe**: Full TypeScript integration with existing API types
- **Responsive**: Mobile-friendly layouts with Material-UI Grid
- **Themed**: Consistent dark theme with project styling

### Performance
- **Lazy rendering**: Only active tab content is rendered
- **Memoized calculations**: Statistical calculations cached per component
- **Efficient updates**: React hooks for state management
- **Chunked data**: Large datasets handled with pagination

### Testing
- **Comprehensive test suite**: 25+ test cases
- **Integration tests**: Cross-component compatibility
- **Edge case handling**: Minimal data scenarios
- **Mock data**: Realistic test scenarios

## Usage Examples

### Basic Integration
```tsx
import { EnhancedPredictionResult } from './components/EnhancedPredictionResult';

<EnhancedPredictionResult 
  result={predictionResponse}
  request={predictionRequest}
  loading={false}
  error={null}
/>
```

### Individual Components
```tsx
import { DeviationMetrics, RecommendationBadges } from './components/quantitative';

<DeviationMetrics result={predictionResponse} />
<RecommendationBadges result={predictionResponse} />
```

### Custom Implementations
```tsx
// Custom risk threshold
const isHighRisk = result.sample_details.maps_used < 10 || 
                   result.confidence < 60 || 
                   result.data_tier > 3;

// Custom edge calculation
const edge = Math.abs(result.expected_stat - result.prop_value);
const edgePercent = (edge / result.prop_value) * 100;
```

## Data Requirements

### Required Fields
- `prediction`: 'OVER' | 'UNDER'
- `confidence`: number (0-100)
- `expected_stat`: number
- `confidence_interval`: [number, number]
- `prop_value`: number
- `sample_details`: SampleDetails object

### Optional Enhancements
- `prediction_curve`: For sensitivity analysis
- `player_stats`: For detailed analytics
- `sample_details.sample_sources`: For source breakdown
- `sample_details.volatility`: For risk calculations

## Customization

### Styling
All components accept Material-UI `sx` props for custom styling:

```tsx
<DeviationMetrics 
  result={result} 
  sx={{ 
    '& .deviation-card': { 
      backgroundColor: 'custom.color' 
    } 
  }} 
/>
```

### Thresholds
Risk and recommendation thresholds can be customized by modifying the component logic:

```tsx
// Custom confidence thresholds
const confidenceThresholds = {
  high: 85,    // vs default 80
  medium: 65,  // vs default 60
  low: 45      // vs default 45
};
```

### Metrics
Additional metrics can be calculated and displayed:

```tsx
// Custom volatility calculation
const customVolatility = (ciWidth / expectedStat) * customMultiplier;
```

## Future Enhancements

### Planned Features
1. **Real-time updates**: Live data refresh capabilities
2. **Historical comparison**: Compare with previous predictions
3. **Custom alerts**: User-defined threshold notifications
4. **Export functionality**: PDF/CSV export of analysis
5. **Advanced visualizations**: 3D risk surfaces, correlation matrices

### Integration Opportunities
1. **Portfolio management**: Multi-bet portfolio analysis
2. **Backtesting**: Historical performance validation
3. **Machine learning**: Advanced model explainability
4. **Social features**: Analyst collaboration tools

---

This quantitative analysis suite transforms basic predictions into professional-grade analytical insights suitable for serious sports betting analysis.