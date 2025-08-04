const { chromium } = require('playwright');

async function testAutocomplete() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  console.log('🚀 Starting autocomplete performance test...');
  
  try {
    // Navigate to the application
    console.log('📱 Navigating to application...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    
    // Wait for the player input field
    console.log('🔍 Finding player search input...');
    const playerInput = await page.waitForSelector('input[placeholder*="search players"]', { timeout: 10000 });
    
    // Test immediate visual feedback
    console.log('⚡ Testing immediate visual feedback...');
    const startTime = Date.now();
    
    // Type a character and measure response time
    await playerInput.type('f');
    
    // Check for loading indicator appears immediately
    const loadingIndicator = await page.waitForSelector('text="Searching players..."', { timeout: 1000 });
    const feedbackTime = Date.now() - startTime;
    
    console.log(`✅ Visual feedback appeared in ${feedbackTime}ms`);
    
    // Continue typing to test full search
    console.log('🔤 Testing full search: "faker"...');
    const searchStartTime = Date.now();
    await playerInput.type('aker');
    
    // Wait for search results
    try {
      await page.waitForSelector('text="matches found"', { timeout: 5000 });
      const searchTime = Date.now() - searchStartTime;
      console.log(`🎯 Search completed in ${searchTime}ms`);
      
      // Check if Faker appears in results
      const fakerResult = await page.waitForSelector('text="Faker"', { timeout: 2000 });
      if (fakerResult) {
        console.log('✅ Found "Faker" in search results');
      }
      
      // Test autocomplete dropdown appears
      const dropdown = await page.waitForSelector('[role="listbox"]', { timeout: 2000 });
      if (dropdown) {
        console.log('✅ Autocomplete dropdown appeared');
        
        // Count visible options
        const options = await page.$$('[role="option"]');
        console.log(`📊 Found ${options.length} autocomplete options`);
      }
      
    } catch (error) {
      console.log('⚠️ Search results took longer than 5 seconds or failed');
    }
    
    // Test typing responsiveness with rapid input
    console.log('⚡ Testing rapid typing responsiveness...');
    await playerInput.clear();
    
    const rapidStartTime = Date.now();
    await playerInput.type('caps', { delay: 50 }); // Type with 50ms between characters
    
    const rapidEndTime = Date.now();
    console.log(`⚡ Rapid typing completed in ${rapidEndTime - rapidStartTime}ms`);
    
    // Check final results
    try {
      await page.waitForSelector('text="matches found"', { timeout: 3000 });
      console.log('✅ Rapid typing search successful');
    } catch (error) {
      console.log('⚠️ Rapid typing search failed or slow');
    }
    
    console.log('🎉 Autocomplete test completed!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  } finally {
    await browser.close();
  }
}

// Run the test
testAutocomplete().catch(console.error);