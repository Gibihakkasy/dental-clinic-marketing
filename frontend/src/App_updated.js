// ... (previous imports remain the same)

  // In the handleGenerate function, replace the comment with:
  
  // Check for cached images for each article
  newProgress.forEach(async (item, idx) => {
    if (item.imagePrompt) {
      try {
        const response = await axios.post('http://localhost:8000/check_cached_image', {
          prompt: item.imagePrompt,
          article_link: item.article_link
        });
        if (response.data.image_url) {
          setProgress(prev => {
            const updated = [...prev];
            updated[idx].imageUrl = response.data.image_url;
            return updated;
          });
        }
      } catch (err) {
        console.error('Error checking for cached image:', err);
      }
    }
  });

  // In the handleProcessTopics function, replace the comment with:
  
  // Check for cached images for each topic
  newProgress.forEach(async (item, idx) => {
    if (item.imagePrompt) {
      try {
        const response = await axios.post('http://localhost:8000/check_cached_image', {
          prompt: item.imagePrompt,
          article_link: item.article_link
        });
        if (response.data.image_url) {
          setProgress(prev => {
            const updated = [...prev];
            updated[idx].imageUrl = response.data.image_url;
            return updated;
          });
        }
      } catch (err) {
        console.error('Error checking for cached image:', err);
      }
    }
  });

// ... (rest of the file remains the same)
