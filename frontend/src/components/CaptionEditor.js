import React, { useState, useEffect, useCallback } from 'react';
import TextareaAutosize from 'react-textarea-autosize';
import { VStack } from '@chakra-ui/react';

const CaptionEditor = ({ 
  caption, 
  onSave
}) => {
  const [editedCaption, setEditedCaption] = useState(caption);
  const [saveTimeout, setSaveTimeout] = useState(null);

  useEffect(() => {
    setEditedCaption(caption);
  }, [caption]);

  const handleCaptionChange = useCallback((e) => {
    const newValue = e.target.value;
    setEditedCaption(newValue);
    if (saveTimeout) {
      clearTimeout(saveTimeout);
    }
    const timeoutId = setTimeout(() => {
      onSave(newValue);
    }, 500);
    setSaveTimeout(timeoutId);
    return () => {
      if (saveTimeout) {
        clearTimeout(saveTimeout);
      }
    };
  }, [onSave, saveTimeout]);

  return (
    <VStack align="stretch" spacing={4} mt={2}>
      <TextareaAutosize
        value={editedCaption}
        onChange={handleCaptionChange}
        minRows={3}
        style={{ width: '100%', fontSize: '1rem', background: 'white', borderRadius: 6, border: '1px solid #CBD5E0', padding: 8, resize: 'none' }}
        placeholder="Edit your caption here..."
      />
    </VStack>
  );
};

export default CaptionEditor;
