import { NextResponse } from 'next/server';

const DJANGO_API_URL = process.env.NEXT_PUBLIC_DJANGO_API_URL || 'http://localhost:8000';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const address = searchParams.get('address');
    
    const response = await fetch(`${DJANGO_API_URL}/api/user-donations/?address=${address}`);
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Failed to fetch user donations:', error);
    return NextResponse.json({ donations: [] }, { status: 500 });
  }
}