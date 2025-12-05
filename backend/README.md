# AdsGenie Backend

FastAPI backend application for AdsGenie with DynamoDB and S3 integration.

## Project Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── api/                      # API routes
│   │   └── v1/
│   │       ├── api.py            # Main API router
│   │       └── endpoints/       # Individual endpoint modules
│   │           ├── health.py
│   │           ├── projects.py
│   │           ├── global_settings.py
│   │           ├── scenes.py
│   │           └── generation.py
│   ├── core/                     # Core configuration
│   │   ├── config.py            # Application settings
│   │   ├── dynamodb.py          # DynamoDB client
│   │   └── s3.py                # S3 client and utilities
│   ├── schemas/                  # Pydantic schemas
│   │   ├── project.py
│   │   ├── global_settings.py
│   │   ├── scene.py
│   │   └── generation.py
│   ├── crud/                     # CRUD operations
│   │   └── project.py
│   ├── services/                 # External service integrations
│   │   ├── ai.py                # NanoBanana & VEO3 integrations
│   │   └── video_stitcher.py
│   └── tasks/                    # Background tasks
│       └── generation.py
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and configure your settings:
```bash
cp .env.example .env
```

4. Set up AWS credentials and configure:
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - S3_BUCKET_NAME
   - DYNAMODB_TABLE_NAME

5. Create DynamoDB table:
   - Table name: `Projects` (or as configured)
   - Partition key: `project_id` (String)

6. Create S3 bucket:
   - Bucket name: `adsgenie-assets` (or as configured)

7. Configure AI service API keys:
   - NANOBANANA_API_KEY
   - VEO3_API_KEY

## Running the Application

Start the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## API Endpoints

### Health
- `GET /health` - Health check
- `GET /api/v1/health` - API health check

### Projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects` - List projects
- `GET /api/v1/projects/{project_id}` - Get project details
- `DELETE /api/v1/projects/{project_id}` - Delete project

### Global Settings
- `PUT /api/v1/projects/{project_id}/global` - Update global character/setting
- `DELETE /api/v1/projects/{project_id}/global/character` - Delete global character
- `DELETE /api/v1/projects/{project_id}/global/setting` - Delete global setting

### Scenes
- `POST /api/v1/projects/{project_id}/scenes` - Add scene
- `PUT /api/v1/projects/{project_id}/scenes/{scene_id}` - Update scene
- `DELETE /api/v1/projects/{project_id}/scenes/{scene_id}` - Delete scene
- `PUT /api/v1/projects/{project_id}/scenes/reorder` - Reorder scenes

### Generation
- `POST /api/v1/projects/{project_id}/scenes/{scene_id}/generate-image` - Generate scene image
- `POST /api/v1/projects/{project_id}/scenes/{scene_id}/generate-video` - Generate scene video
- `DELETE /api/v1/projects/{project_id}/scenes/{scene_id}/generated-image` - Delete generated image
- `DELETE /api/v1/projects/{project_id}/scenes/{scene_id}/generated-video` - Delete generated video
- `POST /api/v1/projects/{project_id}/generate-video` - Generate full project video

## Development

### Local Development with DynamoDB Local

1. Run DynamoDB Local:
```bash
docker run -p 8000:8000 amazon/dynamodb-local
```

2. Set in `.env`:
```
DYNAMODB_ENDPOINT_URL=http://localhost:8000
```

### Local Development with LocalStack (S3)

1. Run LocalStack:
```bash
docker run -p 4566:4566 localstack/localstack
```

2. Set in `.env`:
```
S3_ENDPOINT_URL=http://localhost:4566
```

## Background Tasks

All image and video generation tasks run asynchronously in the background. The frontend should poll `GET /api/v1/projects/{project_id}` to check scene status updates.

Scene status values:
- `pending` - Not yet processed
- `processing` - Currently being generated
- `done` - Successfully generated
- `failed` - Generation failed
