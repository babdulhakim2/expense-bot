import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const { action, ...data } = await req.json();
    
    // Validate action
    if (!['create_link_token', 'exchange_token'].includes(action)) {
      return NextResponse.json(
        { error: 'Invalid action' },
        { status: 400 }
      );
    }

    // Make sure PYTHON_API_URL is properly set and formatted
    const baseUrl = process.env.PYTHON_API_URL || 'http://localhost:9004';
    console.log('Environment:', {
      PYTHON_API_URL: process.env.PYTHON_API_URL,
      NODE_ENV: process.env.NODE_ENV
    });

    console.log(`Making request to: ${baseUrl}/api/banking/plaid/${action}`);

    const response = await fetch(`${baseUrl}/api/banking/plaid/${action}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(data),
    });

    // Check if response is JSON
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      const text = await response.text();
      console.error('Non-JSON response:', text);
      console.error('Response status:', response.status);
      console.error('Response headers:', Object.fromEntries(response.headers.entries()));
      console.error('Request URL:', `${baseUrl}/api/banking/plaid/${action}`);
      throw new Error(`Invalid response from server (${response.status})`);
    }

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || 'Failed to process Plaid request');
    }

    return NextResponse.json(result);

  } catch (error: any) {
    console.error('Plaid API error:', error);
    return NextResponse.json(
      { 
        error: error.message || 'Failed to process request',
        details: process.env.NODE_ENV === 'development' ? error.stack : undefined
      },
      { status: 500 }
    );
  }
} 