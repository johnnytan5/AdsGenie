🧩 FRONTEND SPECIFICATION (FOR ENGINEER)
Project: Ads Genie
Stack (Recommended): Next.js + React + Tailwind + Zustand (or Redux) + ShadCN UI
🟥 0. HIGH-LEVEL USER FLOW

User chooses aspect ratio (16:9 or 9:16)

User creates global settings

Global Character (name, description, sketch/image, generate button)

Global Scene (location/setting description, sketch/image, generate button)

User builds the timeline

Add scene

Each scene has:

Duration (seconds OR auto from text/AI)

Scene description

Sketch/image upload

Image generation button

Drag & drop reorder

User presses “Generate Video”

System sends structured pipeline to backend

NanoBanana + voiceover + timeline assembly begin

Editor mode

For each scene:

Preview generated video

Regenerate scene (image → video)

Edit content / replace sketch / edit text

Delete scene

Save Project → My Projects

Load previous timelines

Continue editing

🟦 1. PAGE STRUCTURE
1. Landing Page

“Create New Project” → leads to aspect ratio screen

“My Projects” button

🟩 2. ASPECT RATIO SELECTION PAGE

Purpose: Pick 16:9 or 9:16 before entering editor.

UI Elements:

Two large cards:

16:9 (YouTube / Desktop Ads)

9:16 (TikTok / Reels)

Each card shows a small preview frame

“Continue” button (disabled until selection made)

State saved:
aspectRatio: "16:9" | "9:16"

🟨 3. PROJECT EDITOR PAGE (CORE UI)
Layout (recommended):
Left sidebar – Global Settings
Main panel – Timeline Scenes
Right panel (optional) – Inspector (scene-specific)
Floating bottom bar – Add Scene / Generate Video

🔶 3.1 GLOBAL SETTINGS (LEFT SIDEBAR)
Section A: Global Character

Fields:

Character Name

Character Description (textarea)

Upload Sketch/Image

“Generate Character Image” button (calls your image → AI image generator)

Preview of final character image

Section B: Global Scene / Setting

Fields:

Setting Name

Setting Description

Upload Sketch/Image

“Generate Scene Image” button

Preview of global setting background

Additional Notes:

These images should be saved as global references, used for character consistency across all scenes.

State Example:
globalSettings: {
  character: {
    name: "",
    description: "",
    image: null // final generated
  },
  setting: {
    name: "",
    description: "",
    image: null
  }
}

🟦 3.2 TIMELINE SCENE BUILDER (MAIN PANEL)
Component: SceneCard

Each scene will show:

Drag handle (for reordering)

Scene Number (auto)

Thumbnail (generated image or placeholder)

Duration input (seconds)

Scene Description

File Upload (sketch/image)

“Generate Image for Scene” button

Remove Scene (trash icon)

Expand/Collapse arrow for advanced settings

Drag & Drop

Use react-beautiful-dnd or @dnd-kit.

State Example:
scenes: [
  {
    id: "uuid",
    order: 1,
    duration: 5,
    description: "Character enters room holding product",
    sketch: null,
    generatedImage: null,
    generatedVideo: null
  }
]

Add Scene

Bottom-bar button:

[ + Add New Scene ]


Inserts a new blank SceneCard.

🟫 3.3 SCENE INSPECTOR PANEL (RIGHT SIDEBAR)

When a scene is selected:

Editable description

Replace sketch/image

Regenerate image

Regenerate video

Playback video preview

🟪 4. VIDEO GENERATION FLOW
Generate Video Button (Fixed bottom bar)
Generate Full Video

What frontend sends to backend:
{
  aspectRatio,
  
  globalCharacter: {
    description,
    image
  },
  globalSetting: {
    description,
    image
  },

  scenes: [
    {
      duration,
      description,
      sketchImage,
      finalImage,
    }
  ]
}

Expected backend outputs per scene:
{
  sceneId: "...",
  videoURL: "https://....mp4",
  imageUsed: "..." // final AI frame
}

Full assembly video also returned.
🟧 5. EDITING MODE (AFTER GENERATION)
For each scene:

Video preview (with a thumbnail timeline)

Regenerate only this scene

Edit description & image prompt

Replace sketch

Click “Apply to scene”

Re-render only that scene and update the assembled video at the end

Important:

Frontend only resends the single scene payload when user regenerates.

🟫 6. MY PROJECTS PAGE

Grid of saved projects:

Thumbnail (use first scene image or video frame)

Project name

Last updated

Aspect ratio

CTA: “Open Project”

Minimal Schema:
Project {
  id: string,
  name: string,
  aspectRatio: string,
  globalSettings: {...},
  scenes: [...],
  updatedAt: Date,
  thumbnail: string
}

🟦 7. RECOMMENDED COMPONENT BREAKDOWN
Components

<ProjectSidebar />

<GlobalSettingsPanel />

<SceneList />

<SceneCard />

<SceneInspector />

<AddSceneButton />

<AspectRatioSelector />

<ProjectHeader />

<VideoPreviewModal />

<MyProjectsGrid />

🟩 8. NON-FUNCTIONAL REQUIREMENTS
Autosave

Autosave every 5 seconds

Manual “Save Project” button

File format support:

PNG/JPG for sketches

MP4 for videos

Error handling:

Generation failures

Missing required fields

API rate limits

Loading UI:

Skeleton loaders

Generation progress bar