'use client';

import { useProjectStore, Scene } from '@/store/projectStore';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  horizontalListSortingStrategy,
} from '@dnd-kit/sortable';
import {
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical } from 'lucide-react';

interface MiniSceneCardProps {
  scene: Scene;
  startTime: number;
  endTime: number;
  isSelected: boolean;
  onSelect: () => void;
}

const MiniSceneCard: React.FC<MiniSceneCardProps> = ({
  scene,
  startTime,
  endTime,
  isSelected,
  onSelect,
}) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: scene.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    if (mins > 0) {
      return `${mins}m ${secs}s`;
    }
    return `${secs}s`;
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex-shrink-0 w-32 h-24 bg-white border-2 rounded-lg cursor-pointer transition-all ${
        isSelected
          ? 'border-blue-500 shadow-md scale-105'
          : 'border-slate-200 hover:border-slate-300'
      }`}
      onClick={onSelect}
    >
      <div className="relative w-full h-full">
        {/* Scene Number Badge */}
        <div className="absolute top-1 right-1 z-10 bg-blue-600 text-white text-xs font-semibold px-1.5 py-0.5 rounded">
          {scene.order}
        </div>

        {/* Thumbnail */}
        <div className="w-full h-full rounded-lg overflow-hidden">
          {scene.generatedImage ? (
            <img
              src={scene.generatedImage}
              alt={`Scene ${scene.order}`}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center">
              <span className="text-slate-400 text-xs">No image</span>
            </div>
          )}
        </div>

        {/* Time Range Overlay */}
        <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-xs px-1.5 py-0.5 rounded-b-lg">
          {formatTime(startTime)} - {formatTime(endTime)}
        </div>

        {/* Drag Handle */}
        <div
          className="absolute top-1 left-1 z-10 bg-white/80 backdrop-blur-sm rounded p-0.5 cursor-grab active:cursor-grabbing"
          {...attributes}
          {...listeners}
          onClick={(e) => e.stopPropagation()}
        >
          <GripVertical className="w-3 h-3 text-slate-600" />
        </div>
      </div>
    </div>
  );
};

interface SceneTimelineProps {
  selectedSceneId: string | null;
  onSelectScene: (id: string | null) => void;
}

export const SceneTimeline: React.FC<SceneTimelineProps> = ({
  selectedSceneId,
  onSelectScene,
}) => {
  const { currentProject, reorderScenes } = useProjectStore();
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  if (!currentProject || currentProject.scenes.length === 0) {
    return null;
  }

  const scenes = currentProject.scenes;

  // Calculate start and end times for each scene
  const sceneTimes = scenes.reduce((acc, scene, index) => {
    const startTime = index === 0 ? 0 : acc[index - 1].endTime;
    const endTime = startTime + scene.duration;
    acc.push({ startTime, endTime });
    return acc;
  }, [] as Array<{ startTime: number; endTime: number }>);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = scenes.findIndex((scene) => scene.id === active.id);
      const newIndex = scenes.findIndex((scene) => scene.id === over.id);
      reorderScenes(oldIndex, newIndex);
    }
  };

  return (
    <div className="flex-1 overflow-x-auto px-4">
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={scenes.map((s) => s.id)}
          strategy={horizontalListSortingStrategy}
        >
          <div className="flex items-center gap-3 h-24 py-2">
            {scenes.map((scene, index) => (
              <MiniSceneCard
                key={scene.id}
                scene={scene}
                startTime={sceneTimes[index].startTime}
                endTime={sceneTimes[index].endTime}
                isSelected={selectedSceneId === scene.id}
                onSelect={() => onSelectScene(scene.id)}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>
    </div>
  );
};

