'use client';

import { useProjectStore, Scene } from '@/store/projectStore';
import { SceneCard } from './SceneCard';
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
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import {
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

interface SortableSceneCardProps {
  scene: Scene;
  index: number;
  isSelected: boolean;
  onSelect: () => void;
}

const SortableSceneCard: React.FC<SortableSceneCardProps> = ({
  scene,
  index,
  isSelected,
  onSelect,
}) => {
  const { updateScene, deleteScene } = useProjectStore();
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

  return (
    <div ref={setNodeRef} style={style}>
      <SceneCard
        scene={scene}
        index={index}
        onUpdate={async (updates) => await updateScene(scene.id, updates)}
        onDelete={async () => await deleteScene(scene.id)}
        isSelected={isSelected}
        onSelect={onSelect}
        dragAttributes={attributes}
        dragListeners={listeners}
      />
    </div>
  );
};

interface SceneListProps {
  selectedSceneId: string | null;
  onSelectScene: (id: string | null) => void;
}

export const SceneList: React.FC<SceneListProps> = ({
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

  if (!currentProject) return null;

  const scenes = currentProject.scenes;

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = scenes.findIndex((scene) => scene.id === active.id);
      const newIndex = scenes.findIndex((scene) => scene.id === over.id);
      await reorderScenes(oldIndex, newIndex);
    }
  };

  if (scenes.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <div className="text-center">
          <p className="text-lg mb-2">No scenes yet</p>
          <p className="text-sm">Click "Add New Scene" to get started</p>
        </div>
      </div>
    );
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={handleDragEnd}
    >
      <SortableContext
        items={scenes.map((s) => s.id)}
        strategy={verticalListSortingStrategy}
      >
        <div className="space-y-4">
          {scenes.map((scene, index) => (
            <SortableSceneCard
              key={scene.id}
              scene={scene}
              index={index}
              isSelected={selectedSceneId === scene.id}
              onSelect={() => onSelectScene(scene.id)}
            />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  );
};

