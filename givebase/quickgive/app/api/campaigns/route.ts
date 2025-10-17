import { NextResponse } from 'next/server';

const DJANGO_API_URL = process.env.NEXT_PUBLIC_DJANGO_API_URL || 'http://localhost:8000';

export async function GET() {
  try {
    const response = await fetch(`${DJANGO_API_URL}/api/campaigns/`);
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Failed to fetch campaigns:', error);
    return NextResponse.json({ campaigns: [] }, { status: 500 });
  }
}