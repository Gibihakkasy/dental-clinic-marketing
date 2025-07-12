import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Textarea, VStack } from '@chakra-ui/react';

const CaptionEditor = ({ 
  caption, 
  onSave
}) => {
  const [editedCaption, setEditedCaption] = useState(caption);
  const [saveTimeout, setSaveTimeout] = useState(null);
  const textareaRef = useRef(null);

  // Update local state when caption prop changes
  useEffect(() => {
    setEditedCaption(caption);
  }, [caption]);

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [editedCaption]);

  // Auto-save after user stops typing for 500ms
  const handleCaptionChange = useCallback((e) => {
    const newValue = e.target.value;
    setEditedCaption(newValue);
    
    // Clear any existing timeout
    if (saveTimeout) {
      clearTimeout(saveTimeout);
    }
    
    // Set a new timeout
    const timeoutId = setTimeout(() => {
      onSave(newValue);
    }, 500);
    
    setSaveTimeout(timeoutId);
    
    // Cleanup function to clear the timeout if the component unmounts
    return () => {
      if (saveTimeout) {
        clearTimeout(saveTimeout);
      }
    };
  }, [onSave, saveTimeout]);

  return (
    <VStack align="stretch" spacing={4} mt={2}>
      <Textarea
        ref={textareaRef}
        value={editedCaption}
        onChange={handleCaptionChange}
        minH="60px"
        maxH="400px"
        overflow="auto"
        placeholder="Edit your caption here..."
        size="sm"
        bg="white"
        resize="none"
      />
    </VStack>
  );
};

export default CaptionEditor;
