# Ads Genie

AI-powered video ad generation platform that creates stunning video advertisements from text descriptions, sketches, and AI-generated images.

## 🎯 Overview

Ads Genie enables users to create professional video ads by:
- Defining global characters and settings for consistency
- Building scene-by-scene timelines with drag-and-drop editing
- Generating AI images using sketch, image coupled with descriptions
- Creating videos on per scene basis
- Supporting both 16:9 (YouTube/Desktop) and 9:16 (TikTok/Reels) aspect ratios

## ✨ Features

- **Aspect Ratio Selection**: Choose between landscape (16:9) or portrait (9:16) formats
- **Global Settings**: Define reusable character and setting assets
- **Scene Builder**: Create and manage multiple scenes with drag-and-drop reordering
- **AI Image Generation**: Generate images from descriptions and sketches
- **Video Generation**: Create individual scene videos and full project assemblies
- **Timeline Editor**: Visual timeline with mini-scene thumbnails for quick navigation
- **Project Management**: Save, load, and manage multiple projects
- **Real-time Preview**: Preview generated videos before export
- **Autosave**: Automatic project saving every 5 seconds

## 🛠 Tech Stack

### Frontend
- **Framework**: Next.js 16 (App Router)
- **UI**: React 19, Tailwind CSS
- **State Management**: Zustand
- **Drag & Drop**: @dnd-kit
- **Icons**: Lucide React
- **Language**: TypeScript

### Backend
- **Framework**: FastAPI
- **Database**: DynamoDB
- **Storage**: AWS S3
- **AI Services**: 
  - NanoBanana (image generation)
  - VEO3.1 (video generation)
- **Video Processing**: FFmpeg

## 📁 Project Structure

```
AdsGenie/
├── frontend/          # Next.js frontend application
│   ├── src/
│   │   ├── app/      # Next.js pages and routes
│   │   ├── components/  # React components
│   │   └── store/    # Zustand state management
│   └── package.json
├── backend/          # FastAPI backend application
│   ├── app/
│   │   ├── api/      # API endpoints
│   │   ├── core/     # Configuration, DynamoDB, S3
│   │   ├── crud/     # Database operations
│   │   ├── schemas/  # Pydantic models
│   │   ├── services/ # Business logic (AI, video)
│   │   └── tasks/    # Background tasks
│   └── requirements.txt
└── docs/             # Documentation
    ├── frontendguide.md
    └── backendEngineerguide.md
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- AWS Account (for DynamoDB and S3)
- API keys for NanoBanana and VEO3.1

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at `http://localhost:3000`

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up environment variables (see backend/.env.example)
cp .env.example .env
# Edit .env with your AWS credentials and API keys

# Run the server
uvicorn app.main:app --reload
```

Backend API will be available at `http://localhost:8000`

## 📖 Usage Workflow

1. **Create Project**: Select aspect ratio (16:9 or 9:16)
2. **Global Settings**: 
   - Define character (name, description, sketch)
   - Define setting (location, description, sketch)
   - Generate AI images for both
3. **Build Timeline**:
   - Add scenes with descriptions and durations
   - Upload sketches or generate images
   - Drag and drop to reorder scenes
4. **Generate Video**:
   - Generate images for all scenes
   - Generate full project video
   - Preview and export final video
5. **Edit & Refine**:
   - Regenerate individual scenes
   - Edit descriptions and replace assets
   - Save project for later editing

## 🔌 API Overview

### Project Management
- `POST /projects` - Create new project
- `GET /projects` - List all projects
- `GET /projects/{project_id}` - Get project details
- `DELETE /projects/{project_id}` - Delete project

### Global Settings
- `PUT /projects/{project_id}/global` - Update character/setting
- `DELETE /projects/{project_id}/global/{character|setting}` - Delete assets

### Scene Management
- `POST /projects/{project_id}/scenes` - Add scene
- `PUT /projects/{project_id}/scenes/{scene_id}` - Update scene
- `DELETE /projects/{project_id}/scenes/{scene_id}` - Delete scene
- `PUT /projects/{project_id}/scenes/reorder` - Reorder scenes

### Generation
- `POST /projects/{project_id}/scenes/{scene_id}/generate-image` - Generate scene image
- `POST /projects/{project_id}/scenes/{scene_id}/generate-video` - Generate scene video
- `POST /projects/{project_id}/generate-video` - Generate full project video

See `docs/backendEngineerguide.md` for complete API documentation.

## 🗄 Data Model

Projects are stored in DynamoDB with the following structure:
- `project_id` (UUID, partition key)
- `name`, `aspect_ratio`
- `global_character`, `global_setting`
- `scenes[]` (array of scene objects)
- `final_video_s3_url`
- `created_at`, `updated_at`

Assets are stored in S3 under `/projects/{project_id}/` with organized subdirectories.

## 🔄 Development

### Frontend Development
- State management: Zustand store in `src/store/projectStore.ts`
- Components: Reusable UI components in `src/components/ui/`
- Pages: Next.js App Router pages in `src/app/`

### Backend Development
- API routes: FastAPI routers in `app/api/v1/endpoints/`
- Database operations: CRUD functions in `app/crud/`
- AI services: Integration in `app/services/ai.py`
- Background tasks: Async processing in `app/tasks/`

## 📚 Documentation

- **Frontend Guide**: `docs/frontendguide.md` - Complete frontend specification
- **Backend Guide**: `docs/backendEngineerguide.md` - Complete backend API and architecture

## 🎨 UI Features

- Clean, minimalistic light theme
- Responsive design
- Drag-and-drop scene reordering (vertical list + horizontal timeline)
- Real-time scene inspector
- Video preview modal with export functionality
- Autosave every 5 seconds

## 🔐 Environment Variables

### Backend (.env)
```
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=
DYNAMODB_TABLE_NAME=
S3_BUCKET_NAME=
NANOBANANA_API_KEY=
VEO_API_KEY=
```

## 📝 License

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines here]

