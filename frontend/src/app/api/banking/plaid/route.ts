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

    const baseUrl = process.env.NEXT_PUBLIC_FLASK_API_URL;

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

  } catch (error) {
    console.error('Plaid API error:', error);
    return NextResponse.json(
      { 
        error: (error && typeof error === 'object' && 'message' in error ? error.message : 'Failed to process request') as string,
        details: process.env.NODE_ENV === 'development' && error && typeof error === 'object' && 'stack' in error ? error.stack : undefined
      },
      { status: 500 }
    );
  }
} 