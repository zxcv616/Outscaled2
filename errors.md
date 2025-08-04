Compiled with problems:
×
ERROR in src/components/enhanced/EnhancedPredictionCurve.tsx:37:11
TS2339: Property 'expectedStat' does not exist on type 'PredictionResponse'.
    35 |   quantMetrics
    36 | }) => {
  > 37 |   const { expectedStat, propValue, confidenceInterval, prediction, confidence } = result;
       |           ^^^^^^^^^^^^
    38 |   const isOver = prediction === 'OVER';
    39 |   
    40 |   // Calculate curve points for visualization
ERROR in src/components/enhanced/EnhancedPredictionCurve.tsx:37:25
TS2339: Property 'propValue' does not exist on type 'PredictionResponse'.
    35 |   quantMetrics
    36 | }) => {
  > 37 |   const { expectedStat, propValue, confidenceInterval, prediction, confidence } = result;
       |                         ^^^^^^^^^
    38 |   const isOver = prediction === 'OVER';
    39 |   
    40 |   // Calculate curve points for visualization
ERROR in src/components/enhanced/EnhancedPredictionCurve.tsx:37:36
TS2339: Property 'confidenceInterval' does not exist on type 'PredictionResponse'.
    35 |   quantMetrics
    36 | }) => {
  > 37 |   const { expectedStat, propValue, confidenceInterval, prediction, confidence } = result;
       |                                    ^^^^^^^^^^^^^^^^^^
    38 |   const isOver = prediction === 'OVER';
    39 |   
    40 |   // Calculate curve points for visualization
ERROR in src/components/enhanced/EnhancedPredictionCurve.tsx:51:9
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element[]; item: true; xs: number; lg: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element[]; item: true; xs: number; lg: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    49 |       <Grid container spacing={3}>
    50 |         {/* Main Sensitivity Chart */}
  > 51 |         <Grid item xs={12} lg={8}>
       |         ^^^^^^^^^^^^^^^^^^^^^^^^^^
    52 |           <Box sx={{ position: 'relative', height: 200, mb: 3 }}>
    53 |             {/* Chart Background */}
    54 |             <Box sx={{
ERROR in src/components/enhanced/EnhancedPredictionCurve.tsx:198:9
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; lg: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; lg: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    196 |         
    197 |         {/* Sensitivity Analysis Stats */}
  > 198 |         <Grid item xs={12} lg={4}>
        |         ^^^^^^^^^^^^^^^^^^^^^^^^^^
    199 |           <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, height: '100%' }}>
    200 |             {/* Turning Point Analysis */}
    201 |             <Paper sx={{
ERROR in src/components/enhanced/EnhancedPredictionResult.tsx:185:11
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & ChipOwnProps & ChipSlotsAndSlotProps & CommonProps & Omit<...>): Element | null', gave the following error.
    Type '"large"' is not assignable to type '"small" | "medium" | undefined'.
  Overload 2 of 2, '(props: DefaultComponentProps<ChipTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '"large"' is not assignable to type '"small" | "medium" | undefined'.
    183 |           label={recommendation.label}
    184 |           color={recommendation.color}
  > 185 |           size="large"
        |           ^^^^
    186 |           sx={{
    187 |             fontSize: '1rem',
    188 |             fontWeight: 600,
ERROR in src/components/enhanced/EnhancedPredictionResult.tsx:198:9
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; md: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; md: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    196 |       {/* Core Metrics Row */}
    197 |       <Grid container spacing={3} sx={{ mb: 4 }}>
  > 198 |         <Grid item xs={12} md={3}>
        |         ^^^^^^^^^^^^^^^^^^^^^^^^^^
    199 |           <Card sx={{ 
    200 |             background: 'rgba(255, 255, 255, 0.05)',
    201 |             border: '1px solid rgba(255, 255, 255, 0.1)',
ERROR in src/components/enhanced/EnhancedPredictionResult.tsx:221:9
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; md: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; md: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    219 |         </Grid>
    220 |         
  > 221 |         <Grid item xs={12} md={3}>
        |         ^^^^^^^^^^^^^^^^^^^^^^^^^^
    222 |           <Card sx={{ 
    223 |             background: 'rgba(255, 255, 255, 0.05)',
    224 |             border: '1px solid rgba(255, 255, 255, 0.1)',
ERROR in src/components/enhanced/EnhancedPredictionResult.tsx:238:9
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; md: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; md: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    236 |         </Grid>
    237 |         
  > 238 |         <Grid item xs={12} md={3}>
        |         ^^^^^^^^^^^^^^^^^^^^^^^^^^
    239 |           <Card sx={{ 
    240 |             background: 'rgba(255, 255, 255, 0.05)',
    241 |             border: '1px solid rgba(255, 255, 255, 0.1)',
ERROR in src/components/enhanced/EnhancedPredictionResult.tsx:255:9
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; md: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; md: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    253 |         </Grid>
    254 |         
  > 255 |         <Grid item xs={12} md={3}>
        |         ^^^^^^^^^^^^^^^^^^^^^^^^^^
    256 |           <Card sx={{ 
    257 |             background: 'rgba(255, 255, 255, 0.05)',
    258 |             border: '1px solid rgba(255, 255, 255, 0.1)',
ERROR in src/components/enhanced/EnhancedPredictionResult.tsx:296:13
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; md: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; md: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    294 |           <Grid container spacing={3}>
    295 |             {/* Prop Value Deviation Metrics */}
  > 296 |             <Grid item xs={12} md={4}>
        |             ^^^^^^^^^^^^^^^^^^^^^^^^^^
    297 |               <Paper sx={{ p: 3, background: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
    298 |                 <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
    299 |                   <Speed sx={{ mr: 1, color: 'secondary.main' }} />
ERROR in src/components/enhanced/EnhancedPredictionResult.tsx:318:13
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; md: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; md: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    316 |
    317 |             {/* Volatility & Risk */}
  > 318 |             <Grid item xs={12} md={4}>
        |             ^^^^^^^^^^^^^^^^^^^^^^^^^^
    319 |               <Paper sx={{ p: 3, background: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
    320 |                 <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
    321 |                   <Timeline sx={{ mr: 1, color: 'warning.main' }} />
ERROR in src/components/enhanced/EnhancedPredictionResult.tsx:348:13
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; md: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; md: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    346 |
    347 |             {/* Contextual Data */}
  > 348 |             <Grid item xs={12} md={4}>
        |             ^^^^^^^^^^^^^^^^^^^^^^^^^^
    349 |               <Paper sx={{ p: 3, background: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
    350 |                 <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
    351 |                   <DataUsage sx={{ mr: 1, color: 'info.main' }} />
ERROR in src/components/enhanced/EnhancedPredictionResult.tsx:482:15
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element[]; item: true; xs: number; md: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element[]; item: true; xs: number; md: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    480 |             </Typography>
    481 |             <Grid container spacing={2}>
  > 482 |               <Grid item xs={12} md={6}>
        |               ^^^^^^^^^^^^^^^^^^^^^^^^^^
    483 |                 <Box sx={{ mb: 2 }}>
    484 |                   <Typography variant="body2" color="text.secondary">Model Version</Typography>
    485 |                   <Typography variant="body1">v2.1.3 (Primary Model)</Typography>
ERROR in src/components/enhanced/EnhancedPredictionResult.tsx:496:15
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; md: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; md: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    494 |                 </Box>
    495 |               </Grid>
  > 496 |               <Grid item xs={12} md={6}>
        |               ^^^^^^^^^^^^^^^^^^^^^^^^^^
    497 |                 <Box sx={{ mb: 2 }}>
    498 |                   <Typography variant="body2" color="text.secondary">Top Feature Drivers</Typography>
    499 |                   <Typography variant="body1">
ERROR in src/components/quantitative/ContextualDataSnapshot.tsx:229:9
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; md: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; md: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    227 |       <Grid container spacing={2} sx={{ mb: 3 }}>
    228 |         {/* Temporal Context */}
  > 229 |         <Grid item xs={12} md={6}>
        |         ^^^^^^^^^^^^^^^^^^^^^^^^^^
    230 |           <Card sx={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.1)', height: '100%' }}>
    231 |             <CardContent sx={{ p: 2 }}>
    232 |               <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
ERROR in src/components/quantitative/ContextualDataSnapshot.tsx:269:9
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; md: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; md: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    267 |
    268 |         {/* Sample Context */}
  > 269 |         <Grid item xs={12} md={6}>
        |         ^^^^^^^^^^^^^^^^^^^^^^^^^^
    270 |           <Card sx={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.1)', height: '100%' }}>
    271 |             <CardContent sx={{ p: 2 }}>
    272 |               <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
ERROR in src/components/quantitative/ContextualDataSnapshot.tsx:309:9
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; md: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; md: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    307 |
    308 |         {/* Environmental Context */}
  > 309 |         <Grid item xs={12} md={6}>
        |         ^^^^^^^^^^^^^^^^^^^^^^^^^^
    310 |           <Card sx={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.1)', height: '100%' }}>
    311 |             <CardContent sx={{ p: 2 }}>
    312 |               <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
ERROR in src/components/quantitative/ContextualDataSnapshot.tsx:349:9
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; md: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; md: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    347 |
    348 |         {/* Methodological Context */}
  > 349 |         <Grid item xs={12} md={6}>
        |         ^^^^^^^^^^^^^^^^^^^^^^^^^^
    350 |           <Card sx={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.1)', height: '100%' }}>
    351 |             <CardContent sx={{ p: 2 }}>
    352 |               <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
ERROR in src/components/quantitative/ContextualDataSnapshot.tsx:400:17
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; sm: number; md: number; key: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; sm: number; md: number; key: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    398 |             <Grid container spacing={1}>
    399 |               {sampleSources.map((source, index) => (
  > 400 |                 <Grid item xs={12} sm={6} md={4} key={index}>
        |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    401 |                   <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 1 }}>
    402 |                     <Typography variant="body2">{source.name}</Typography>
    403 |                     <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
ERROR in src/components/quantitative/DataIntegrityFlags.tsx:266:11
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; key: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; key: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    264 |       <Grid container spacing={3}>
    265 |         {integrityFlags.map((flag, index) => (
  > 266 |           <Grid item xs={12} key={index}>
        |           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    267 |             <Card
    268 |               sx={{
    269 |                 background: 'rgba(255, 255, 255, 0.03)',
ERROR in src/components/quantitative/DeviationMetrics.tsx:137:11
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; md: number; key: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; md: number; key: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    135 |       <Grid container spacing={2}>
    136 |         {deviationMetrics.map((metric, index) => (
  > 137 |           <Grid item xs={12} md={4} key={index}>
        |           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    138 |             <Card
    139 |               sx={{
    140 |                 background: 'rgba(255, 255, 255, 0.03)',
ERROR in src/components/quantitative/RecommendationBadges.tsx:426:11
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; sm: number; key: string; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; sm: number; key: string; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    424 |       <Grid container spacing={2}>
    425 |         {recommendations.map((badge) => (
  > 426 |           <Grid item xs={12} sm={6} key={badge.id}>
        |           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    427 |             <Card
    428 |               sx={{
    429 |                 background: badge.backgroundColor,
ERROR in src/components/quantitative/SensitivityCurve.tsx:157:9
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; md: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; md: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    155 |       {/* Sensitivity Metrics */}
    156 |       <Grid container spacing={2} sx={{ mb: 3 }}>
  > 157 |         <Grid item xs={12} md={3}>
        |         ^^^^^^^^^^^^^^^^^^^^^^^^^^
    158 |           <Card sx={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
    159 |             <CardContent sx={{ textAlign: 'center', p: 2 }}>
    160 |               <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
ERROR in src/components/quantitative/SensitivityCurve.tsx:176:9
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; md: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; md: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    174 |         </Grid>
    175 |
  > 176 |         <Grid item xs={12} md={3}>
        |         ^^^^^^^^^^^^^^^^^^^^^^^^^^
    177 |           <Card sx={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
    178 |             <CardContent sx={{ textAlign: 'center', p: 2 }}>
    179 |               <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
ERROR in src/components/quantitative/SensitivityCurve.tsx:189:9
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; md: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; md: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    187 |         </Grid>
    188 |
  > 189 |         <Grid item xs={12} md={3}>
        |         ^^^^^^^^^^^^^^^^^^^^^^^^^^
    190 |           <Card sx={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
    191 |             <CardContent sx={{ textAlign: 'center', p: 2 }}>
    192 |               <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
ERROR in src/components/quantitative/SensitivityCurve.tsx:202:9
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; md: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; md: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    200 |         </Grid>
    201 |
  > 202 |         <Grid item xs={12} md={3}>
        |         ^^^^^^^^^^^^^^^^^^^^^^^^^^
    203 |           <Card sx={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
    204 |             <CardContent sx={{ textAlign: 'center', p: 2 }}>
    205 |               <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
ERROR in src/components/quantitative/VolatilityRiskClassification.tsx:198:9
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; md: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; md: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    196 |       {/* Risk Components */}
    197 |       <Grid container spacing={3} sx={{ mb: 3 }}>
  > 198 |         <Grid item xs={12} md={4}>
        |         ^^^^^^^^^^^^^^^^^^^^^^^^^^
    199 |           <Card sx={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
    200 |             <CardContent sx={{ p: 2 }}>
    201 |               <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
ERROR in src/components/quantitative/VolatilityRiskClassification.tsx:220:9
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; md: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; md: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    218 |         </Grid>
    219 |
  > 220 |         <Grid item xs={12} md={4}>
        |         ^^^^^^^^^^^^^^^^^^^^^^^^^^
    221 |           <Card sx={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
    222 |             <CardContent sx={{ p: 2 }}>
    223 |               <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
ERROR in src/components/quantitative/VolatilityRiskClassification.tsx:242:9
TS2769: No overload matches this call.
  Overload 1 of 2, '(props: { component: ElementType<any, keyof IntrinsicElements>; } & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<...> & Omit<...>): Element | null', gave the following error.
    Property 'component' is missing in type '{ children: Element; item: true; xs: number; md: number; }' but required in type '{ component: ElementType<any, keyof IntrinsicElements>; }'.
  Overload 2 of 2, '(props: DefaultComponentProps<GridTypeMap<{}, "div">>): Element | null', gave the following error.
    Type '{ children: Element; item: true; xs: number; md: number; }' is not assignable to type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
      Property 'item' does not exist on type 'IntrinsicAttributes & GridBaseProps & { sx?: SxProps<Theme> | undefined; } & SystemProps<Theme> & Omit<...>'.
    240 |         </Grid>
    241 |
  > 242 |         <Grid item xs={12} md={4}>
        |         ^^^^^^^^^^^^^^^^^^^^^^^^^^
    243 |           <Card sx={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
    244 |             <CardContent sx={{ p: 2 }}>
    245 |               <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>