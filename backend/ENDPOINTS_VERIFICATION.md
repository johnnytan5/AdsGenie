# Backend Endpoints Verification

## ✅ All endpoints verified to use:
- **Google GenAI API** (for NanoBanana image generation & VEO3 video generation)
- **AWS S3** (for file storage)
- **AWS DynamoDB** (for data persistence)

---

## 📋 Endpoint Summary

### 1. Project Management (`/api/v1/projects`)

#### ✅ POST `/api/v1/projects` - Create Project
- **DynamoDB**: ✅ Creates project in DynamoDB via `crud_project.create_project()`
- **S3**: N/A (no files at creation)
- **Google GenAI**: N/A

#### ✅ GET `/api/v1/projects` - List Projects
- **DynamoDB**: ✅ Reads from DynamoDB via `crud_project.list_projects()`
- **S3**: N/A
- **Google GenAI**: N/A

#### ✅ GET `/api/v1/projects/{project_id}` - Get Project
- **DynamoDB**: ✅ Reads from DynamoDB via `crud_project.get_project()`
- **S3**: N/A
- **Google GenAI**: N/A

#### ✅ DELETE `/api/v1/projects/{project_id}` - Delete Project
- **DynamoDB**: ✅ Deletes from DynamoDB via `crud_project.delete_project()`
- **S3**: ✅ Deletes all project files via `delete_prefix_from_s3()`
- **Google GenAI**: N/A

---

### 2. Global Settings (`/api/v1/projects/{project_id}/global`)

#### ✅ PUT `/api/v1/projects/{project_id}/global` - Update Global Settings
- **DynamoDB**: ✅ Updates via `crud_project.update_global_settings()` and `update_global_character_s3_urls()` / `update_global_setting_s3_urls()`
- **S3**: ✅ Uploads sketches via `upload_file_to_s3()`
- **Google GenAI**: ✅ Generates images via background task `generate_global_character_image_task()` / `generate_global_setting_image_task()` using `generate_image_nanobanana()`

#### ✅ DELETE `/api/v1/projects/{project_id}/global/character` - Delete Global Character
- **DynamoDB**: ✅ Updates via `crud_project.delete_global_character()`
- **S3**: ✅ Deletes files via `delete_file_from_s3()`
- **Google GenAI**: N/A

#### ✅ DELETE `/api/v1/projects/{project_id}/global/setting` - Delete Global Setting
- **DynamoDB**: ✅ Updates via `crud_project.delete_global_setting()`
- **S3**: ✅ Deletes files via `delete_file_from_s3()`
- **Google GenAI**: N/A

---

### 3. Scene Management (`/api/v1/projects/{project_id}/scenes`)

#### ✅ POST `/api/v1/projects/{project_id}/scenes` - Add Scene
- **DynamoDB**: ✅ Creates scene via `crud_project.add_scene()`
- **S3**: ✅ Uploads sketch via `upload_file_to_s3()` if provided
- **Google GenAI**: N/A

#### ✅ PUT `/api/v1/projects/{project_id}/scenes/{scene_id}` - Update Scene
- **DynamoDB**: ✅ Updates via `crud_project.update_scene()`
- **S3**: ✅ Uploads new sketch via `upload_file_to_s3()` if provided
- **Google GenAI**: N/A

#### ✅ DELETE `/api/v1/projects/{project_id}/scenes/{scene_id}` - Delete Scene
- **DynamoDB**: ✅ Deletes via `crud_project.delete_scene()`
- **S3**: ✅ Deletes all scene files (sketch, image, video) via `delete_file_from_s3()`
- **Google GenAI**: N/A

#### ✅ PUT `/api/v1/projects/{project_id}/scenes/reorder` - Reorder Scenes
- **DynamoDB**: ✅ Updates via `crud_project.reorder_scenes()`
- **S3**: N/A
- **Google GenAI**: N/A

---

### 4. Image/Video Generation (`/api/v1/projects/{project_id}/scenes/{scene_id}/generate-*`)

#### ✅ POST `/api/v1/projects/{project_id}/scenes/{scene_id}/generate-image` - Generate Scene Image
- **DynamoDB**: ✅ Reads project via `crud_project.get_project()`, updates via `update_scene_generated_image()`
- **S3**: ✅ Uploads generated image via `upload_file_to_s3()` in background task
- **Google GenAI**: ✅ Uses `generate_image_nanobanana()` (Gemini 2.5 Flash Image) via background task `generate_scene_image_task()`

#### ✅ POST `/api/v1/projects/{project_id}/scenes/{scene_id}/generate-video` - Generate Scene Video
- **DynamoDB**: ✅ Reads project via `crud_project.get_project()`, updates via `update_scene_generated_video()`
- **S3**: ✅ Uploads generated video via `upload_file_to_s3()` in background task
- **Google GenAI**: ✅ Uses `generate_video_veo3()` (VEO 3.1) via background task `generate_scene_video_task()` with reference images

#### ✅ DELETE `/api/v1/projects/{project_id}/scenes/{scene_id}/generated-image` - Delete Generated Image
- **DynamoDB**: ✅ Updates via `crud_project.delete_scene_generated_image()`
- **S3**: ✅ Deletes file via `delete_file_from_s3()`
- **Google GenAI**: N/A

#### ✅ DELETE `/api/v1/projects/{project_id}/scenes/{scene_id}/generated-video` - Delete Generated Video
- **DynamoDB**: ✅ Updates via `crud_project.delete_scene_generated_video()`
- **S3**: ✅ Deletes file via `delete_file_from_s3()`
- **Google GenAI**: N/A

#### ✅ POST `/api/v1/projects/{project_id}/generate-video` - Generate Full Project Video
- **DynamoDB**: ✅ Reads/updates via `crud_project.get_project()` and `update_final_video()`
- **S3**: ✅ Uses scene videos from S3, uploads final video via `upload_file_to_s3()`
- **Google GenAI**: ✅ Generates scene videos via `generate_scene_video_task()` using VEO 3.1

---

## 🔍 Service Usage Details

### Google GenAI API Usage:
- **Image Generation**: `gemini-2.5-flash-image` model
  - Text-and-image-to-image (when sketch provided)
  - Text-to-image fallback (when no sketch)
  - Used in: Global character/setting image generation, Scene image generation

- **Video Generation**: `veo-3.1-generate-preview` model
  - Uses reference images (scene image + optional global character/setting)
  - Async operation with polling
  - Used in: Scene video generation

### AWS S3 Usage:
- **Uploads**: All file uploads use `upload_file_to_s3()`
  - Sketches (character, setting, scene)
  - Generated images (character, setting, scene)
  - Generated videos (scene, final)

- **Deletes**: All file deletions use `delete_file_from_s3()` or `delete_prefix_from_s3()`
  - Individual file deletion
  - Bulk deletion (project deletion)

### AWS DynamoDB Usage:
- **All CRUD operations** use `get_projects_table()` from `app.core.dynamodb`
- **Table**: `Projects` (configurable via `DYNAMODB_TABLE_NAME`)
- **Partition Key**: `project_id`
- **Operations**: Create, Read, Update, Delete for projects, scenes, global settings

---

## ✅ Verification Complete

All endpoints are properly integrated with:
- ✅ Google GenAI API (Google Studio API)
- ✅ AWS S3
- ✅ AWS DynamoDB

No endpoints are using mock or placeholder implementations.
