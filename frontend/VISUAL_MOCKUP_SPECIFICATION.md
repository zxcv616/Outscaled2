# Visual Mockup Specification - Enhanced Prediction Results

## Layout Structure & Visual Hierarchy

### Overall Container
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Enhanced Prediction Results                             │
│                          Glass Morphism Card                                │
│                      Elevation: 24, Blur: 20px                             │
│                   Border: 1px solid rgba(255,255,255,0.1)                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Section 1: Prediction Header (Height: 120px)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [🎯]  OVER              4.4 Expected Kills          [🏷️ Smart OVER]      │
│  48x48  H4 Bold          Body Text                   Med Chip w/ Icon      │
│  Green   87% Confidence  Prop: 7.0                  Success Color         │
│  Grad.   Body Secondary  H3 Bold                     High Confidence       │
│         Box              Box                                              │
│                                                     [Copy JSON] [Settings] │
│                                                     Outlined   Icon Btn    │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Design Elements:**
- **Prediction Icon**: 48x48px circular gradient background with trend icon
- **Confidence**: Large percentage with semantic color coding
- **Recommendation Badge**: Prominent chip with risk classification
- **Action Buttons**: Right-aligned, subtle but accessible

### Section 2: Core Metrics Grid (Height: 160px)
```
┌─────────────┬─────────────┬─────────────┬─────────────────────────────────┐
│ CONFIDENCE  │  EXPECTED   │  PROP LINE  │      Z-SCORE                   │
│             │             │             │                                │
│    87%      │    4.4      │     7.0     │       +1.84                    │
│   H3 Bold   │   H3 Bold   │   H3 Bold   │      H3 Bold                   │
│             │             │             │                                │
│    HIGH     │   Kills     │             │   93rd percentile              │
│ Success Chip│ Secondary   │             │   Caption Secondary            │
│             │   Text      │             │                                │
│ Linear Prog │             │             │   Tooltip: "Statistical       │
│   87%       │             │             │   distance from mean"          │
└─────────────┴─────────────┴─────────────┴─────────────────────────────────┘
```

**Card Styling:**
- **Background**: rgba(255,255,255,0.05)
- **Border**: 1px solid rgba(255,255,255,0.1)
- **Padding**: 24px
- **Border Radius**: 8px

### Section 3: Quantitative Analytics (Expandable - Height: Variable)
```
┌─ 📊 Quantitative Analytics ────────────────── [▼] ─────────────────────────┐
│                                                                            │
│ ┌──────────────────┬─────────────────────┬────────────────────────────────┐ │
│ │ Deviation Metrics│ Volatility Analysis │    Context Snapshots          │ │
│ │                  │                     │                               │ │
│ │ Percentile Rank  │ Volatility          │ Last 3 Games                  │ │
│ │  93rd percentile │  38.5% (Moderate)   │  8.0 avg kills                │ │
│ │                  │                     │                               │ │
│ │ Prop/Expected    │ Historical Hit Rate │ vs Gen.G (2024)               │ │
│ │  1.59 ratio      │  71%                │  6.2 avg kills                │ │
│ │                  │                     │                               │ │
│ │ Statistical Gap  │ Volatility Trend    │ Team Kill Rate                │ │
│ │  2.6 (37%)       │  🟢 Stable          │  1.15x league avg             │ │
│ └──────────────────┴─────────────────────┴────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

**Expandable Design:**
- **Accordion Pattern**: Smooth expand/collapse animation
- **Icon Indicators**: Speed, Timeline, DataUsage icons for each section
- **Nested Cards**: Sub-sections with subtle background differences

### Section 4: Enhanced Sensitivity Curve (Height: 300px)
```
┌─ 📈 Prediction Sensitivity Analysis ─────────────────────────────────────────┐
│                                                                              │
│ ┌─────────────────────────────────────┬────────────────────────────────────┐ │
│ │ Confidence │     ╭───╮              │  🎯 Turning Point Analysis        │ │
│ │    100%    │    ╱     ╲             │     Prediction flips at:          │ │
│ │     75%    │   ╱       ╲            │        8.2                        │ │
│ │     50%    │  ╱         ╲           │     UNDER favored above           │ │
│ │     25%    │ ╱           ╲          │                                   │ │
│ │      0%    │╱_____________╲_______   │  📊 Prediction Strength           │ │
│ │            2.0   4.4  7.0   10.0    │     Stability window: ±1.8       │ │
│ │                 ↑     ↑             │     🟢 Stable                     │ │
│ │               Exp   Prop            │                                   │ │
│ │                                     │  📋 Sensitivity Metrics          │ │
│ │ Legend:                             │     Confidence at Prop: 87%      │ │
│ │ ── Prop Line  ── Expected           │     Range Coverage: 20 points     │ │
│ │ ── Confidence ●  Turning Point      │                                   │ │
│ └─────────────────────────────────────┴────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

**SVG Chart Features:**
- **Smooth Curve**: Cubic bezier interpolation for professional appearance
- **Interactive Elements**: Hover states for data points
- **Reference Lines**: Dashed lines for prop and expected values
- **Gradient Fill**: Subtle area fill under confidence curve
- **Responsive Design**: Scales properly on mobile devices

### Section 5: Data Integrity Indicators (Height: 80px)
```
┌─ 🛡️ Data Integrity Status ─────────────────────────────────────────────────┐
│                                                                             │
│ [✅ Full Match Data] [✅ Strict: ON] [ℹ️ Tier 1: 44 maps] [📊 87% Complete] │
│  Success Outlined    Success Outlined  Info Outlined       Success Outlined │
│                                                                             │
│ [⚠️ High Volatility] [🔄 Cache: Fresh] [⚡ Process: 1.2s]                   │
│  Warning Outlined     Info Outlined      Info Outlined                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Chip Design System:**
- **Colors**: Success (green), Warning (orange), Info (blue), Error (red)
- **Variants**: Outlined style for less visual weight
- **Icons**: Meaningful symbols for quick recognition
- **Grouping**: Related indicators grouped with consistent spacing

### Section 6: AI Reasoning (Height: Variable)
```
┌─ 🧠 AI Reasoning ───────────────────────────────────────────────────────────┐
│                                                                             │
│ Using Default Tier for prediction. ⚠️ High volatility detected - recent     │
│ performance shows unusual variability. Expected stat (4.4) within          │
│ historical range: 3.9 to 8.8. Below-average recent form. Good sample      │
│ size for reliable prediction.                                              │
│                                                                             │
│ 🔑 Key Factors:                                                             │
│ • Recent Performance (62% influence) ████████████▓▓▓▓▓                      │
│ • Position Factor (21% influence)    ████▓▓▓▓▓▓▓▓▓▓▓▓▓                      │
│ • Opponent Meta (14% influence)      ███▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Content Design:**
- **Typography**: Body text with 1.6 line height for readability
- **Emphasis**: Important values highlighted with bold weight
- **Warning Callouts**: ⚠️ symbols for risk factors
- **Progress Bars**: Visual representation of feature importance
- **Structured Lists**: Bullet points for key factors

### Section 7: Technical Metadata (Expandable - Height: Variable)
```
┌─ 🔬 Technical Metadata ────────────────────── [👁️ Show] ──────────────────────┐
│                                                                             │
│ ┌─────────────────────┬─────────────────────┬─────────────────────────────┐ │
│ │ Model Details       │ Performance Metrics │ Data Pipeline               │ │
│ │                     │                     │                             │ │
│ │ Version: v2.1.3     │ Training: 2024-07-15│ Updated: 2h ago             │ │
│ │ Mode: Primary       │ Validation R²: 0.847│ Cache: Fresh                │ │
│ │ CI Method: Bootstrap│ Cross-val: 0.823    │ Processing: 1.2s            │ │
│ │                     │                     │                             │ │
│ │ Feature Engineering │ Model Performance   │ Debug Information          │ │
│ │ Lookback: 90 days   │ Accuracy: 84.7%     │ Memory: 2.1MB               │ │
│ │ Filters: Position   │ Precision: 0.891    │ Threads: 4                  │ │
│ │ Transforms: Log     │ Recall: 0.778       │ GPU: Disabled               │ │
│ └─────────────────────┴─────────────────────┴─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Collapsible Design:**
- **Show/Hide Button**: Toggle button with eye icon
- **Detailed Grid**: 3-column layout for comprehensive information
- **Monospace Font**: Technical values in monospace for consistency
- **Subtle Background**: Even more muted background for technical details

## Color System & Semantic Meaning

### Primary Colors:
- **Success Green**: #4caf50 - OVER predictions, positive indicators, high confidence
- **Error Red**: #f44336 - UNDER predictions, high risk, critical warnings
- **Warning Orange**: #ff9800 - Moderate risk, volatility alerts, medium confidence
- **Info Blue**: #2196f3 - Neutral information, secondary metrics
- **Primary Purple**: #3f51b5 - Interactive elements, charts, primary actions

### Background Colors:
- **Card Background**: rgba(26, 26, 26, 0.95) - Main container
- **Sub-card Background**: rgba(255, 255, 255, 0.05) - Metric cards
- **Nested Background**: rgba(255, 255, 255, 0.02) - Technical metadata
- **Chart Background**: Linear gradients for visual appeal

### Text Colors:
- **Primary Text**: rgba(255, 255, 255, 0.87) - Main content
- **Secondary Text**: rgba(255, 255, 255, 0.6) - Labels and descriptions
- **Disabled Text**: rgba(255, 255, 255, 0.38) - Inactive elements

## Typography Scale:

### Headers:
- **H3**: 32px, Bold, 1.2 line height - Primary metrics
- **H4**: 24px, Bold, 1.3 line height - Section headers
- **H5**: 20px, Medium, 1.4 line height - Subsection headers
- **H6**: 16px, Medium, 1.5 line height - Card titles

### Body Text:
- **Body 1**: 14px, Regular, 1.6 line height - Main content
- **Body 2**: 12px, Regular, 1.5 line height - Secondary content
- **Caption**: 10px, Regular, 1.4 line height - Fine print

## Spacing System (8px Base Unit):

### Padding:
- **Major Sections**: 32px (4 units)
- **Cards**: 24px (3 units)
- **Sub-components**: 16px (2 units)
- **Small Elements**: 8px (1 unit)

### Margins:
- **Section Separation**: 32px
- **Card Separation**: 16px
- **Element Separation**: 8px
- **Tight Grouping**: 4px

## Interactive States:

### Hover Effects:
- **Cards**: Subtle brightness increase (+5%)
- **Buttons**: Background color shift with smooth transition
- **Chart Elements**: Highlight with increased opacity

### Focus States:
- **Keyboard Navigation**: Clear focus indicators with brand colors
- **Screen Readers**: Proper ARIA labels and descriptions

### Loading States:
- **Skeleton Placeholders**: Animated shimmer effect
- **Progressive Loading**: Core metrics first, then details
- **Error Recovery**: Clear error messages with retry options

## Responsive Breakpoints:

### Desktop (1200px+):
- Full layout with 4-column metrics grid
- Side-by-side chart and analysis sections
- All advanced features visible

### Tablet (768px - 1199px):
- 2x2 metrics grid
- Stacked chart and analysis sections
- Collapsible advanced sections

### Mobile (< 768px):
- Single column layout
- Swipe-able metric cards
- Bottom sheet for advanced details
- Touch-optimized interactive elements

This visual specification provides the complete blueprint for implementing the enhanced prediction results interface with professional quantitative analysis capabilities.