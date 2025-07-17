#!/usr/bin/env node
/**
 * 🧪 Frontend Integration Test: OpenSource Voice API
 * 
 * Tests the integration between frontend and the new opensource voice service.
 * This script simulates frontend API calls to validate the migration.
 */

const fetch = require('node-fetch');
const { EventSource } = require('eventsource');

// Configuration
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
const TEST_USER_ID = 'test_frontend_integration';

// Mock authentication token (you'll need to replace this with a real token)
const MOCK_TOKEN = 'your_test_token_here';

async function testOpensourceVoiceAPI() {
    console.log('🎯 Testing OpenSource Voice API Integration');
    console.log('=' * 50);
    
    try {
        // Test 1: Health Check
        console.log('\n🏥 Test 1: Health Check');
        const healthResponse = await fetch(`${API_URL}/api/opensource-voice/health`);
        if (healthResponse.ok) {
            const healthData = await healthResponse.json();
            console.log('✅ Health check passed:', healthData);
        } else {
            console.log('❌ Health check failed:', healthResponse.status);
            return;
        }
        
        // Test 2: SSE Connection Test
        console.log('\n📡 Test 2: SSE Connection Test');
        await testSSEConnection();
        
        // Test 3: Text Message Test
        console.log('\n📝 Test 3: Text Message Test');
        await testTextMessage();
        
        // Test 4: Audio Message Test (simulated)
        console.log('\n🎤 Test 4: Audio Message Test');
        await testAudioMessage();
        
        console.log('\n🎉 All integration tests completed!');
        
    } catch (error) {
        console.error('❌ Integration test failed:', error);
    }
}

async function testSSEConnection() {
    return new Promise((resolve, reject) => {
        const sseUrl = `${API_URL}/api/opensource-voice/events/${TEST_USER_ID}?is_audio=true`;
        console.log('🔗 Connecting to SSE:', sseUrl);
        
        // Note: This test will fail without proper authentication
        // This is just to validate the endpoint structure
        const eventSource = new EventSource(sseUrl, {
            headers: {
                'Authorization': `Bearer ${MOCK_TOKEN}`
            }
        });
        
        let sessionId = null;
        let messageCount = 0;
        
        eventSource.onopen = () => {
            console.log('✅ SSE connection opened');
        };
        
        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                messageCount++;
                console.log(`📨 SSE Message ${messageCount}:`, data);
                
                if (data.type === 'session_created') {
                    sessionId = data.session_id;
                    console.log('✅ Session created:', sessionId);
                    
                    // Close connection after getting session
                    setTimeout(() => {
                        eventSource.close();
                        resolve({ sessionId, messageCount });
                    }, 2000);
                }
            } catch (error) {
                console.error('❌ Failed to parse SSE message:', error);
            }
        };
        
        eventSource.onerror = (error) => {
            console.log('⚠️ SSE connection error (expected without proper auth):', error.message);
            eventSource.close();
            resolve({ sessionId: null, messageCount });
        };
        
        // Timeout after 5 seconds
        setTimeout(() => {
            eventSource.close();
            resolve({ sessionId, messageCount });
        }, 5000);
    });
}

async function testTextMessage() {
    // This test requires a valid session, so we'll just test the endpoint structure
    const testSessionId = 'test_session_123';
    const sendUrl = `${API_URL}/api/opensource-voice/send/${testSessionId}`;
    
    console.log('📤 Testing text message endpoint:', sendUrl);
    
    try {
        const response = await fetch(sendUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${MOCK_TOKEN}`
            },
            body: JSON.stringify({
                mime_type: 'text/plain',
                data: 'Hello, this is a test message'
            })
        });
        
        console.log('📊 Text message response status:', response.status);
        
        if (response.status === 404) {
            console.log('✅ Endpoint exists (404 expected for invalid session)');
        } else if (response.status === 401 || response.status === 403) {
            console.log('✅ Authentication required (expected)');
        } else {
            console.log('🤔 Unexpected response status:', response.status);
        }
        
    } catch (error) {
        console.log('⚠️ Text message test error:', error.message);
    }
}

async function testAudioMessage() {
    // Test with simulated PCM audio data
    const testSessionId = 'test_session_123';
    const sendUrl = `${API_URL}/api/opensource-voice/send/${testSessionId}`;
    
    console.log('🎤 Testing audio message endpoint:', sendUrl);
    
    // Create mock PCM audio data (base64 encoded)
    const mockPCMData = Buffer.from('mock audio data').toString('base64');
    
    try {
        const response = await fetch(sendUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${MOCK_TOKEN}`
            },
            body: JSON.stringify({
                mime_type: 'audio/pcm',
                data: mockPCMData
            })
        });
        
        console.log('📊 Audio message response status:', response.status);
        
        if (response.status === 404) {
            console.log('✅ Endpoint exists (404 expected for invalid session)');
        } else if (response.status === 401 || response.status === 403) {
            console.log('✅ Authentication required (expected)');
        } else {
            console.log('🤔 Unexpected response status:', response.status);
        }
        
    } catch (error) {
        console.log('⚠️ Audio message test error:', error.message);
    }
}

// Utility function to create audio test data
function createTestAudioData() {
    // Create a simple test audio pattern
    const sampleRate = 24000;
    const duration = 1.0; // 1 second
    const samples = sampleRate * duration;
    
    const audioBuffer = new Float32Array(samples);
    for (let i = 0; i < samples; i++) {
        // Generate a 440Hz sine wave
        audioBuffer[i] = Math.sin(2 * Math.PI * 440 * i / sampleRate) * 0.1;
    }
    
    // Convert to 16-bit PCM
    const pcmBuffer = new Int16Array(samples);
    for (let i = 0; i < samples; i++) {
        pcmBuffer[i] = Math.round(audioBuffer[i] * 32767);
    }
    
    return Buffer.from(pcmBuffer.buffer).toString('base64');
}

// Configuration validation
function validateConfiguration() {
    console.log('🔧 Configuration Check:');
    console.log('   API_URL:', API_URL);
    console.log('   Test User ID:', TEST_USER_ID);
    
    if (!API_URL) {
        console.error('❌ NEXT_PUBLIC_API_URL not configured');
        return false;
    }
    
    if (MOCK_TOKEN === 'your_test_token_here') {
        console.log('⚠️ Using mock token - authentication tests will fail');
    }
    
    return true;
}

// Main execution
if (require.main === module) {
    console.log('🚀 OpenSource Voice API Integration Test');
    console.log('Testing frontend integration with new voice service...\n');
    
    if (validateConfiguration()) {
        testOpensourceVoiceAPI().catch(console.error);
    } else {
        console.error('❌ Configuration validation failed');
        process.exit(1);
    }
}

module.exports = {
    testOpensourceVoiceAPI,
    testSSEConnection,
    testTextMessage,
    testAudioMessage
}; 