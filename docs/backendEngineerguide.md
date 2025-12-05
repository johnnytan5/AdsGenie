🧩 Backend Engineer Guide – Ads Genie

Stack: FastAPI + DynamoDB + S3
AI Services: NanoBanana (images), VEO3.1 (video)

0️⃣ Data Models
DynamoDB Table: Projects

Partition key: project_id (UUID)

Attributes:

{
  "project_id": "string",
  "name": "string",
  "aspect_ratio": "16:9|9:16",
  "global_character": {
    "description": "string",
    "sketch_s3_url": "string",
    "generated_image_s3_url": "string"
  },
  "global_setting": {
    "description": "string",
    "sketch_s3_url": "string",
    "generated_image_s3_url": "string"
  },
  "scenes": [
    {
      "scene_id": "string",
      "order": 1,
      "duration": 5,
      "description": "string",
      "sketch_s3_url": "string",
      "generated_image_s3_url": "string",
      "generated_video_s3_url": "string",
      "status": "pending|processing|done|failed"
    }
  ],
  "final_video_s3_url": "string",
  "created_at": "ISO8601 timestamp",
  "updated_at": "ISO8601 timestamp"
}

1️⃣ S3 Storage Structure
/projects/{project_id}/global/character_sketch.png
/projects/{project_id}/global/character_image.png
/projects/{project_id}/global/setting_sketch.png
/projects/{project_id}/global/setting_image.png
/projects/{project_id}/scenes/{scene_id}/sketch.png
/projects/{project_id}/scenes/{scene_id}/generated_image.png
/projects/{project_id}/scenes/{scene_id}/generated_video.mp4
/projects/{project_id}/final_video.mp4

2️⃣ Endpoints
Project Management
2.1 Create Project
POST /projects


Request:

{
  "name": "string",
  "aspect_ratio": "16:9|9:16"
}


Response:

{
  "project_id": "string",
  "name": "string",
  "aspect_ratio": "string"
}

2.2 List Projects
GET /projects


Response:

[
  {
    "project_id": "string",
    "name": "string",
    "thumbnail_s3_url": "string",
    "updated_at": "ISO8601 timestamp"
  }
]

2.3 Get Project Details
GET /projects/{project_id}


Response:

{
  "project_id": "string",
  "name": "string",
  "aspect_ratio": "string",
  "global_character": {...},
  "global_setting": {...},
  "scenes": [...],
  "final_video_s3_url": "...",
  "created_at": "...",
  "updated_at": "..."
}

2.4 Delete Project
DELETE /projects/{project_id}


Delete project entry from DynamoDB

Delete all S3 assets (global + scenes + final video)

Response: 204 No Content

Global Settings
2.5.0  Update Global Character / Setting
PUT /projects/{project_id}/global


Request:

{
  "character": {
    "description": "string",
    "sketch_file": "<file>"  // optional
  },
  "setting": {
    "description": "string",
    "sketch_file": "<file>"  // optional
  }
}


Response:

{
  "global_character": {
    "description": "...",
    "sketch_s3_url": "...",
    "generated_image_s3_url": "..."
  },
  "global_setting": {
    "description": "...",
    "sketch_s3_url": "...",
    "generated_image_s3_url": "..."
  }
}

2.5.1 POST Request for global sketch/image

2.6 Delete Global Sketch/Image
DELETE /projects/{project_id}/global/character
DELETE /projects/{project_id}/global/setting


Notes:

Delete sketch and generated image from S3

Set DynamoDB fields to null

Response: 204 No Content

Scene Management
2.7 Add Scene
POST /projects/{project_id}/scenes


Request:

{
  "description": "string",
  "duration": 5,
  "sketch_file": "<file>"
}


Response:

{
  "scene_id": "string",
  "description": "...",
  "duration": 5,
  "sketch_s3_url": "...",
  "status": "pending"
}

2.8 Update Scene
PUT /projects/{project_id}/scenes/{scene_id}


Request:

{
  "description": "string",
  "duration": 7,
  "sketch_file": "<file>"
}


Response:

{
  "scene_id": "string",
  "description": "...",
  "duration": 7,
  "sketch_s3_url": "...",
  "status": "pending"
}


Note: Update triggers regeneration if any input changed.

2.9 Delete Scene
DELETE /projects/{project_id}/scenes/{scene_id}


Delete sketch, generated image, generated video from S3

Remove scene from DynamoDB array

Response: 204 No Content

2.10 Reorder Scenes
PUT /projects/{project_id}/scenes/reorder


Request:

{
  "scene_order": [
    {"scene_id": "uuid1", "order": 1},
    {"scene_id": "uuid2", "order": 2}
  ]
}


Response:

{
  "success": true
}

Image / Video Generation
2.11 Generate Image for Scene
POST /projects/{project_id}/scenes/{scene_id}/generate-image


Request:

{
  "use_global_character": true,
  "use_global_setting": true
}


Response:

{
  "scene_id": "string",
  "generated_image_s3_url": "...",
  "status": "done"
}

2.12 Generate Video for Scene
POST /projects/{project_id}/scenes/{scene_id}/generate-video


Request:

{
  "aspect_ratio": "16:9",
  "voiceover_text": "optional text",
  "use_global_character": true,
  "use_global_setting": true
}


Response:

{
  "scene_id": "string",
  "generated_video_s3_url": "...",
  "status": "done"
}

2.13 Delete Scene Generated Image / Video
DELETE /projects/{project_id}/scenes/{scene_id}/generated-image
DELETE /projects/{project_id}/scenes/{scene_id}/generated-video


Notes:

Removes from S3

Resets field in DynamoDB (generated_image_s3_url or generated_video_s3_url)

Sets status=pending for regeneration if needed

Response: 204 No Content

2.14 Generate Full Project Video
POST /projects/{project_id}/generate-video


Request:

{
  "aspect_ratio": "16:9"
}


Workflow:

Ensure all scenes have generated_image_s3_url

Generate per-scene videos if missing

Stitch using FFmpeg / VEO3.1

Upload final video to S3

Update DynamoDB final_video_s3_url

Response:

{
  "project_id": "string",
  "final_video_s3_url": "...",
  "status": "done"
}

3️⃣ Async / Background Tasks

All image/video generation should be backgrounded

Suggested: FastAPI BackgroundTasks or Celery/RQ

Frontend polls GET /projects/{project_id} for scene status updates

4️⃣ Frontend Integration Notes

Use S3 URLs from DynamoDB for previews

status allows frontend to display loaders

Drag & drop → PUT /projects/{project_id}/scenes/reorder

Regenerate → POST /generate-image / POST /generate-video

Delete images/videos → respective DELETE endpoints

5️⃣ Recommended Flow

Create project → set aspect ratio

Upload global character / setting → generate AI images

Add scenes → sketch + description → generate scene images

Generate scene videos individually (optional: on-demand)

Reorder, edit scenes as needed

Generate full video → display / download

Save project → My Projects page