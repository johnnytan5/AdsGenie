'use client';

import React, { useRef } from 'react';
import { Button } from './Button';

interface FileUploadProps {
  accept?: string;
  onChange: (file: File | null) => void;
  currentFile?: File | null;
  label?: string;
  className?: string;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  accept = 'image/*',
  onChange,
  currentFile,
  label = 'Upload File',
  className = '',
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    onChange(file);
  };

  return (
    <div className={className}>
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        onChange={handleChange}
        className="hidden"
      />
      <Button
        variant="outline"
        size="sm"
        onClick={handleClick}
        className="w-full"
      >
        {currentFile ? currentFile.name : label}
      </Button>
    </div>
  );
};

