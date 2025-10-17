import { NextResponse } from 'next/server';

const DJANGO_API_URL = process.env.NEXT_PUBLIC_DJANGO_API_URL || 'http://localhost:8000';

export async function GET() {
  try {
    const response = await fetch(`${DJANGO_API_URL}/api/stats/`);
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Failed to fetch stats:', error);
    return NextResponse.json({
      total_donated: '0',
      total_donors: 0,
      sub_account_donations: 0,
      sub_account_percentage: 0
    }, { status: 500 });
  }
}