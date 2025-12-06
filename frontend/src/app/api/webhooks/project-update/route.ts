import { NextRequest, NextResponse } from 'next/server';

// In-memory store for webhooks (in production, use Redis or similar)
// This is a simple solution for development
const webhookStore = new Map<string, { project_id: string; task_type: string; status: string; presigned_url?: string; timestamp: number }>();

/**
 * Webhook endpoint for backend to notify frontend of task completion
 * POST /api/webhooks/project-update
 * Body: { project_id: string, task_type: string, status?: string }
 * 
 * Stores the webhook and dispatches a custom event that client can listen to.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { project_id, task_type, status, presigned_url } = body;
    
    if (!project_id || !task_type) {
      return NextResponse.json(
        { error: 'Missing required fields: project_id and task_type' },
        { status: 400 }
      );
    }

    // Log the webhook for debugging
    console.log(`Webhook received: ${task_type} for project ${project_id} with status ${status || 'done'}${presigned_url ? ' (with presigned URL)' : ''}`);
    
    // Store the webhook (keyed by project_id + task_type for easy lookup)
    const key = `${project_id}:${task_type}`;
    webhookStore.set(key, {
      project_id,
      task_type,
      status: status || 'done',
      presigned_url,
      timestamp: Date.now(),
    });

    // Clean up old webhooks (older than 1 minute)
    const oneMinuteAgo = Date.now() - 60000;
    for (const [k, v] of webhookStore.entries()) {
      if (v.timestamp < oneMinuteAgo) {
        webhookStore.delete(k);
      }
    }

    // Return success with webhook data
    return NextResponse.json({ 
      success: true,
      message: 'Webhook received',
      project_id,
      task_type,
      status: status || 'done'
    });
  } catch (error) {
    console.error('Webhook error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * GET endpoint to check for webhooks (client calls this to check for updates)
 * Query params: project_id, task_type (optional)
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const project_id = searchParams.get('project_id');
  const task_type = searchParams.get('task_type');

  if (!project_id) {
    return NextResponse.json(
      { error: 'Missing project_id parameter' },
      { status: 400 }
    );
  }

  // Return all webhooks for this project, or specific task_type if provided
  const webhooks: Array<{ project_id: string; task_type: string; status: string; presigned_url?: string; timestamp: number }> = [];
  
  for (const [key, webhook] of webhookStore.entries()) {
    if (webhook.project_id === project_id) {
      if (!task_type || webhook.task_type === task_type) {
        webhooks.push(webhook);
        // Remove the webhook after it's been retrieved (one-time use)
        webhookStore.delete(key);
      }
    }
  }

  return NextResponse.json({ webhooks });
}
