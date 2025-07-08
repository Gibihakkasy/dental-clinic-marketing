import React, { useState, useEffect, useRef } from 'react';
import { 
  Box, 
  Flex, 
  Button, 
  Text, 
  Spinner, 
  Link, 
  Checkbox, 
  HStack, 
  VStack, 
  Divider,
  useToast,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  Textarea,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Input,
  IconButton
} from '@chakra-ui/react';
import { DeleteIcon, RepeatIcon } from '@chakra-ui/icons';
import { FaInstagram } from 'react-icons/fa';
import axios from 'axios';
import CaptionEditor from './components/CaptionEditor';
import { FormattedText } from './utils/formatText';

function App() {
  // Helper to fetch cached image URL for a prompt
  const fetchCachedImageUrl = async (prompt) => {
    try {
      const response = await axios.post('http://localhost:8000/generate_image_gpt', {
        prompt,
        force_regenerate: false,
      });
      return response.data.image_url || '';
    } catch {
      return '';
    }
  };

  // Generate image using GPT for article or topic
  const handleGenerateImageGPT = async (articleIdx, force = false) => {
    try {
      setProgress(prev => {
        const newProgress = [...prev];
        newProgress[articleIdx].isGeneratingImage = true;
        return newProgress;
      });
      const article = progress[articleIdx];
      const response = await axios.post('http://localhost:8000/generate_image_gpt', {
        prompt: article.imagePrompt,
        article_link: article.article_link,
        force_regenerate: force,
      });
      setProgress(prev => {
        const newProgress = [...prev];
        newProgress[articleIdx].imageUrl = response.data.image_url;
        newProgress[articleIdx].isGeneratingImage = false;
        return newProgress;
      });
      toast({
        title: force ? 'Image regenerated' : 'Image generated',
        status: 'success',
        duration: 2000,
        isClosable: true,
      });
    } catch (err) {
      setProgress(prev => {
        const newProgress = [...prev];
        if (newProgress[articleIdx]) newProgress[articleIdx].isGeneratingImage = false;
        return newProgress;
      });
      toast({
        title: 'Failed to generate image',
        description: err.response?.data?.detail || err.message,
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  // Article states
  const [groupedArticles, setGroupedArticles] = useState([]); // [{feed_title, feed_url, articles: [{title, link, ...}]}]
  const [selected, setSelected] = useState([]); // [{feed_url, article_link}]
  const [progress, setProgress] = useState([]); // [{status, summary, caption, imagePrompt, feed_url, article_link, title}]
  const [generating, setGenerating] = useState(false);
  const [isPosting, setIsPosting] = useState(false);
  const [selectedForInstagram, setSelectedForInstagram] = useState({});
  const [filename, setFilename] = useState(null);
  const [error, setError] = useState(null);
  
  // Topic states
  const [activeTab, setActiveTab] = useState('articles');
  const [topics, setTopics] = useState([]);
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [customTopic, setCustomTopic] = useState('');
  const [topicGenerationId, setTopicGenerationId] = useState(null);
  const [isGeneratingTopic, setIsGeneratingTopic] = useState(false);
  
  const { isOpen, onClose } = useDisclosure();
  const toast = useToast();
  const containerRef = useRef(null);

  // Fetch initial data on load
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        // Fetch articles
        const [articlesResponse, topicsResponse] = await Promise.all([
          axios.get('http://localhost:8000/get_rss_articles_grouped'),
          axios.get('http://localhost:8000/topics')
        ]);
        
        setGroupedArticles(articlesResponse.data);
        setTopics(topicsResponse.data);
      } catch (err) {
        console.error('Error fetching initial data:', err);
        setError('Failed to load data. Please try again later.');
      }
    };
    
    fetchInitialData();
  }, []);
  
  // Poll for topic generation status
  useEffect(() => {
    if (!topicGenerationId) return;
    
    const checkStatus = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/topics/${topicGenerationId}/status`);
        
        if (response.data.status === 'completed') {
          // Add the new topic to the list
          setTopics(prev => [{
            id: response.data.id,
            topic: response.data.topic,
            preview: response.data.summary.substring(0, 100) + (response.data.summary.length > 100 ? '...' : ''),
            created_at: response.data.created_at
          }, ...prev]);
          
          // Reset generation state
          setTopicGenerationId(null);
          setIsGeneratingTopic(false);
          
          toast({
            title: 'Topic content generated!',
            status: 'success',
            duration: 3000,
            isClosable: true,
          });
          
        } else if (response.data.status === 'error') {
          setTopicGenerationId(null);
          setIsGeneratingTopic(false);
          
          toast({
            title: 'Error generating topic content',
            description: response.data.error || 'An unknown error occurred',
            status: 'error',
            duration: 5000,
            isClosable: true,
          });
        } else {
          // Still processing, check again in 1 second
          setTimeout(checkStatus, 1000);
        }
      } catch (err) {
        console.error('Error checking topic generation status:', err);
        setTopicGenerationId(null);
        setIsGeneratingTopic(false);
        
        toast({
          title: 'Error checking generation status',
          description: err.message,
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
      }
    };
    
    const timerId = setTimeout(checkStatus, 1000);
    return () => clearTimeout(timerId);
  }, [topicGenerationId, toast]);

  // Handle selection
  const handleSelect = (feed_url, article_link, checked, title) => {
    if (checked) {
      setSelected(prev => [...prev, { feed_url, article_link, title }]);
    } else {
      setSelected(prev => prev.filter(s => !(s.feed_url === feed_url && s.article_link === article_link)));
    }
  };

  // Regenerate summary for article or topic
  const handleRegenerateSummary = async (articleIdx, item, isTopic = false) => {
    try {
      // Show loading for summary regeneration
      if (isTopic) {
        setTopics(prev => prev.map(t => t.id === item.id ? { ...t, isRegeneratingSummary: true } : t));
      } else {
        setProgress(prev => {
          const newProgress = [...prev];
          newProgress[articleIdx].isRegenerating = {
            ...newProgress[articleIdx].isRegenerating,
            summary: true
          };
          return newProgress;
        });
      }
      let response;
      if (isTopic) {
        response = await axios.post('http://localhost:8000/regenerate_summary', {
          topic_id: item.id
        });
      } else {
        response = await axios.post('http://localhost:8000/regenerate_summary', {
          article_link: item.article_link
        });
      }
      // Update UI with new summary
      if (isTopic) {
        setTopics(prev => prev.map(t => t.id === item.id ? { ...t, summary: response.data.summary, isRegeneratingSummary: false } : t));
        toast({
          title: 'Topic summary regenerated',
          status: 'success',
          duration: 2000,
          isClosable: true,
        });
      } else {
        setProgress(prev => {
          const newProgress = [...prev];
          newProgress[articleIdx].summary = response.data.summary;
          newProgress[articleIdx].cache_status = {
            ...newProgress[articleIdx].cache_status,
            summary: response.data.cache_status
          };
          newProgress[articleIdx].isRegenerating = {
            ...newProgress[articleIdx].isRegenerating,
            summary: false
          };
          return newProgress;
        });
        toast({
          title: 'Summary regenerated',
          status: 'success',
          duration: 2000,
          isClosable: true,
        });
      }
    } catch (err) {
      toast({
        title: 'Failed to regenerate summary',
        description: err.response?.data?.detail || err.message,
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      if (isTopic) {
        setTopics(prev => prev.map(t => t.id === item.id ? { ...t, isRegeneratingSummary: false } : t));
      } else {
        setProgress(prev => {
          const newProgress = [...prev];
          if (newProgress[articleIdx]) {
            newProgress[articleIdx].isRegenerating = {
              ...(newProgress[articleIdx].isRegenerating || {}),
              summary: false
            };
          }
          return newProgress;
        });
      }
    }
  };

  // Generate plan for selected articles
  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    setFilename(null);
    setProgress(selected.map(sel => ({ ...sel, status: 'pending', summary: '', caption: '', imagePrompt: '', imageUrl: '', isGeneratingImage: false })));
    try {
      const resp = await axios.post('http://localhost:8000/generate_social_plan', { selected });
      // The backend returns {file, grouped}
      if (resp.data && resp.data.grouped) {
        // Flatten selected articles with their results
        let newProgress = [];
        for (const feed of resp.data.grouped) {
          for (const article of feed.articles) {
            const sel = selected.find(s => s.feed_url === feed.feed_url && s.article_link === article.link);
            if (sel) {
              newProgress.push({
                ...sel,
                status: 'done',
                summary: article.summary,
                caption: article.caption,
                imagePrompt: article.imagePrompt,
                imageUrl: '',
                isGeneratingImage: false,
                cache_status: article.cache_status || {
                  caption: false,
                  imagePrompt: false
                },
                isRegenerating: {
                  caption: false,
                  imagePrompt: false
                }
              });
            }
          }
        }
        setProgress(newProgress);

        // Check for cached images for each article
        newProgress.forEach(async (item, idx) => {
          if (item.imagePrompt) {
            try {
              const response = await axios.post("http://localhost:8000/check_cached_image", {
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
              console.error("Error checking for cached image:", err);
            }
          }
        });


        setFilename(resp.data.file);
      } else {
        setError('No grouped data returned from backend.');
      }
    } catch (err) {
      setError('Error generating plan: ' + (err.response?.data?.detail || err.message));
    } finally {
      setGenerating(false);
    }
  };

  const handleRegenerate = async (articleIdx, type) => {
    try {
      // Update progress to show loading state
      setProgress(prev => {
        const newProgress = [...prev];
        newProgress[articleIdx].isRegenerating = {
          ...newProgress[articleIdx].isRegenerating,
          [type]: true
        };
        return newProgress;
      });

      const article = progress[articleIdx];
      let response;
      
      if (type === 'caption') {
        response = await axios.post('http://localhost:8000/regenerate_caption', {
          article_link: article.article_link
        });
      } else if (type === 'imagePrompt') {
        response = await axios.post('http://localhost:8000/regenerate_image_prompt', {
          article_link: article.article_link
        });
      }

      // Update progress with new content
      setProgress(prev => {
        const newProgress = [...prev];
        if (type === 'caption') {
          newProgress[articleIdx].caption = response.data.caption;
        } else if (type === 'imagePrompt') {
          newProgress[articleIdx].imagePrompt = response.data.image_prompt;
        }
        newProgress[articleIdx].cache_status = {
          ...newProgress[articleIdx].cache_status,
          [type]: false // Newly generated content is not from cache
        };
        newProgress[articleIdx].isRegenerating = {
          ...newProgress[articleIdx].isRegenerating,
          [type]: false
        };
        return newProgress;
      });

      toast({
        title: `${type === 'caption' ? 'Caption' : 'Image prompt'} regenerated`,
        status: 'success',
        duration: 2000,
        isClosable: true,
      });
    } catch (err) {
      console.error(`Error regenerating ${type}:`, err);
      toast({
        title: `Failed to regenerate ${type}`,
        description: err.response?.data?.detail || err.message,
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      
      // Reset loading state on error
      setProgress(prev => {
        const newProgress = [...prev];
        if (newProgress[articleIdx]) {
          newProgress[articleIdx].isRegenerating = {
            ...(newProgress[articleIdx].isRegenerating || {}),
            [type]: false
          };
        }
        return newProgress;
      });
    }
  };

  const getStatusDisplay = (status) => {
    if (status === 'pending') return <HStack><Spinner size="xs" /> <span>Generating...</span></HStack>;
    if (status === 'done') return <span style={{ color: 'green' }}>Done</span>;
    if (status === 'error') return <span style={{ color: 'red' }}>Error</span>;
    return status;
  };

  const allDone = progress.length > 0 && progress.every(p => p.status === 'done');

  // Handle topic generation
  const handleGenerateFromTopic = async () => {
    if (!customTopic.trim()) {
      toast({
        title: 'Please enter a topic',
        status: 'warning',
        duration: 2000,
        isClosable: true,
      });
      return;
    }
    
    setIsGeneratingTopic(true);
    setError(null);
    
    try {
      const response = await axios.post('http://localhost:8000/topics/generate', {
        topic: customTopic.trim()
      });
      
      setTopicGenerationId(response.data.generation_id);
      setCustomTopic('');
      
      toast({
        title: 'Generating content for topic...',
        status: 'info',
        duration: 2000,
        isClosable: true,
      });
      
    } catch (err) {
      console.error('Error generating from topic:', err);
      setIsGeneratingTopic(false);
      
      toast({
        title: 'Error generating content',
        description: err.response?.data?.detail || err.message,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };
  
  // Handle topic selection
  const handleTopicSelect = (topicId, isSelected) => {
    setSelectedTopics(prev => 
      isSelected 
        ? [...prev, topicId]
        : prev.filter(id => id !== topicId)
    );
  };
  
  // Handle topic deletion
  const handleDeleteTopic = async (topicId, e) => {
    e.stopPropagation();
    
    try {
      await axios.delete(`http://localhost:8000/topics/${topicId}`);
      
      // Remove from local state
      setTopics(prev => prev.filter(t => t.id !== topicId));
      setSelectedTopics(prev => prev.filter(id => id !== topicId));
      
      toast({
        title: 'Topic deleted',
        status: 'success',
        duration: 2000,
        isClosable: true,
      });
    } catch (err) {
      console.error('Error deleting topic:', err);
      
      toast({
        title: 'Error deleting topic',
        description: err.response?.data?.detail || err.message,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };
  
  // Process selected topics
  const handleProcessTopics = async () => {
    if (selectedTopics.length === 0) return;
    
    setGenerating(true);
    setError(null);
    setFilename(null);
    
    try {
      // Get details for all selected topics
      const topicPromises = selectedTopics.map(topicId => 
        axios.get(`http://localhost:8000/topics/${topicId}`)
      );
      
      const topicResponses = await Promise.all(topicPromises);
      const topicData = topicResponses.map(res => res.data);
      
      // Format the data to match the expected progress format
      const newProgress = topicData.map(topic => ({
        title: topic.topic,
        article_link: `topic:${topic.id}`,
        status: 'done',
        summary: topic.summary,
        caption: topic.caption,
        imagePrompt: topic.image_prompt,
        imageUrl: '',
        isGeneratingImage: false,
        cache_status: {
          summary: true,
          caption: true,
          imagePrompt: true
        },
        isRegenerating: {
          caption: false,
          imagePrompt: false
        }
      }));
      
      setProgress(newProgress);
      
      // Check for cached images for each topic
      newProgress.forEach(async (item, idx) => {
        if (item.imagePrompt) {
          try {
            const response = await axios.post("http://localhost:8000/check_cached_image", {
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
            console.error("Error checking for cached image:", err);
          }
        }
      });

      // Generate a filename for the document
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      setFilename(`topics_${timestamp}.docx`);
      
    } catch (err) {
      console.error('Error processing topics:', err);
      setError('Failed to process topics: ' + (err.response?.data?.detail || err.message));
    } finally {
      setGenerating(false);
    }
  };

  return (
    <Flex direction="column" align="center" justify="center" minH="100vh" bg="gray.900" py={8}>
      <Box
        ref={containerRef}
        bg="white"
        p={8}
        borderRadius={16}
        boxShadow="lg"
        minW={{ base: '90%', md: '800px' }}
        maxW="1200px"
        textAlign="center"
        maxH="90vh"
        overflowY="auto"
      >
        <Text fontSize="2xl" fontWeight="bold" mb={6} color="teal.600">
          Dental Clinic Social Media Planner
        </Text>
        
        <Tabs 
          isFitted 
          variant="enclosed"
          index={activeTab === 'articles' ? 0 : 1}
          onChange={(index) => setActiveTab(index === 0 ? 'articles' : 'topics')}
          mb={6}
        >
          <TabList>
            <Tab _selected={{ color: 'white', bg: 'teal.500' }}>Articles</Tab>
            <Tab _selected={{ color: 'white', bg: 'teal.500' }}>Topics</Tab>
          </TabList>
          
          <TabPanels>
            {/* Articles Tab */}
            <TabPanel p={0} pt={4}>
              {groupedArticles.length > 0 ? (
                <>
                  <Text mb={4} color="gray.700">
                    Select articles to generate Instagram content:
                  </Text>
                  <VStack align="stretch" spacing={4} mb={6} divider={<Divider />}>
                    {groupedArticles.map((feed, fidx) => (
                      <Box key={fidx} textAlign="left">
                        <Text fontWeight="bold" color="teal.700" mb={2}>{feed.feed_title}</Text>
                        {feed.articles.map((a, idx) => (
                          <Box key={a.link} mb={1}>
                            <Checkbox
                              isChecked={selected.some(s => s.feed_url === feed.feed_url && s.article_link === a.link)}
                              onChange={e => handleSelect(feed.feed_url, a.link, e.target.checked, a.title)}
                            >
                              <Link href={a.link} color="blue.500" isExternal>{a.title}</Link>
                            </Checkbox>
                          </Box>
                        ))}
                      </Box>
                    ))}
                  </VStack>
                </>
              ) : (
                <Text color="gray.500" textAlign="center" py={4}>
                  No articles available. Please check your RSS feed configuration.
                </Text>
              )}
              <Button
                colorScheme="teal"
                size="lg"
                onClick={handleGenerate}
                isLoading={generating}
                loadingText="Generating..."
                mb={4}
                isDisabled={selected.length === 0}
              >
                Generate Content ({selected.length} selected)
              </Button>
            </TabPanel>
            
            {/* Topics Tab */}
            <TabPanel p={0} pt={4}>
              <Box mb={4}>
                <HStack>
                  <Input
                    placeholder="Enter a topic (e.g., 'latest dental implant technology')"
                    value={customTopic}
                    onChange={(e) => setCustomTopic(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleGenerateFromTopic()}
                  />
                  <Button 
                    colorScheme="teal" 
                    onClick={handleGenerateFromTopic}
                    isLoading={isGeneratingTopic}
                    loadingText="Generating..."
                    isDisabled={!customTopic.trim()}
                  >
                    Generate
                  </Button>
                </HStack>
              </Box>
              
              <Box borderWidth={1} borderRadius="md" p={4} mb={4} maxH="300px" overflowY="auto">
                {topics.length > 0 ? (
                  <VStack align="stretch" spacing={2}>
                    {topics.map((topic) => (
                      <Box 
                        key={topic.id}
                        borderWidth={1} 
                        borderRadius="md" 
                        p={3}
                        bg={selectedTopics.includes(topic.id) ? 'teal.50' : 'white'}
                        borderColor={selectedTopics.includes(topic.id) ? 'teal.200' : 'gray.200'}
                        cursor="pointer"
                        _hover={{ bg: selectedTopics.includes(topic.id) ? 'teal.100' : 'gray.50' }}
                        onClick={() => handleTopicSelect(topic.id, !selectedTopics.includes(topic.id))}
                      >
                        <Flex justify="space-between" align="center">
                          <Box flex="1" textAlign="left">
                            <HStack>
                              <Checkbox 
                                isChecked={selectedTopics.includes(topic.id)}
                                onChange={(e) => {
                                  e.stopPropagation();
                                  handleTopicSelect(topic.id, e.target.checked);
                                }}
                                onClick={(e) => e.stopPropagation()}
                              >
                                <Text fontWeight="medium">{topic.topic}</Text>
                              </Checkbox>
                            </HStack>
                            <Text fontSize="sm" color="gray.600" mt={1} noOfLines={1}>
                              {topic.preview}
                            </Text>
                            <Text fontSize="xs" color="gray.500" mt={1}>
                              {new Date(topic.created_at * 1000).toLocaleString()}
                            </Text>
                            <Button
                              size="xs"
                              colorScheme="blue"
                              variant="outline"
                              mt={2}
                              onClick={e => {
                                e.stopPropagation();
                                handleRegenerateSummary(null, topic, true);
                              }}
                              leftIcon={<RepeatIcon />}
                            >
                              Regenerate Summary
                            </Button>
                          </Box>
                          <IconButton
                            icon={<DeleteIcon />}
                            size="sm"
                            variant="ghost"
                            colorScheme="red"
                            aria-label="Delete topic"
                            onClick={(e) => handleDeleteTopic(topic.id, e)}
                          />
                        </Flex>
                      </Box>
                    ))}
                  </VStack>
                ) : (
                  <Text color="gray.500" textAlign="center" py={4}>
                    No topics yet. Enter a topic above to get started.
                  </Text>
                )}
              </Box>
              
              <Button
                colorScheme="teal"
                size="lg"
                onClick={handleProcessTopics}
                isLoading={generating}
                loadingText="Processing..."
                mb={4}
                isDisabled={selectedTopics.length === 0}
                width="100%"
              >
                Process Selected Topics ({selectedTopics.length})
              </Button>
            </TabPanel>
          </TabPanels>
        </Tabs>
        
        {error && (
          <Text color="red.500" mb={4}>
            {error}
          </Text>
        )}
        <Box textAlign="left" mt={6}>
          {progress.map((p, idx) => (
            <Box key={idx} mb={8} p={4} borderWidth={1} borderRadius={8} bg="white">
              <Box mb={4}>
                <Text fontSize="lg" fontWeight="bold" mb={2}>
                  {p.title}
                  {p.cache_status?.summary && (
                    <Text as="span" fontSize="sm" color="gray.500" ml={2}>
                      (from cache)
                    </Text>
                  )}
                </Text>
                <HStack spacing={2}>
                  <FaInstagram color="#E1306C" />
                  <Checkbox
                    colorScheme="pink"
                    isChecked={selectedForInstagram[p.article_link] || false}
                    onChange={(e) => {
                      setSelectedForInstagram(prev => ({
                        ...prev,
                        [p.article_link]: e.target.checked
                      }));
                    }}
                    colorScheme="pink"
                  >
                    Post this caption
                  </Checkbox>
                </HStack>
              </Box>
              {p.summary && (
                <Box mb={4} p={4} borderWidth={1} borderRadius="md" bg="gray.50">
                  <HStack justify="space-between" mb={2}>
                    <Text fontWeight="bold">
                      Summary:
                      {p.cache_status?.summary && (
                        <Text as="span" fontSize="sm" color="gray.500" ml={2}>
                          (from cache)
                        </Text>
                      )}
                    </Text>
                    <Button
                      size="xs"
                      colorScheme="blue"
                      variant="outline"
                      onClick={() => handleRegenerateSummary(idx, p)}
                      isLoading={p.isRegenerating?.summary}
                      loadingText="Regenerating..."
                      leftIcon={<RepeatIcon />}
                    >
                      Regenerate
                    </Button>
                  </HStack>
                  <FormattedText text={p.summary} />
                </Box>
              )}
              {p.caption && (
                <Box mb={4} p={4} borderWidth={1} borderRadius="md" bg="gray.50">
                  <HStack justify="space-between" mb={2}>
                    <Text fontWeight="bold">
                      IG Caption:
                      {p.cache_status?.caption && (
                        <Text as="span" fontSize="sm" color="gray.500" ml={2}>
                          (from cache)
                        </Text>
                      )}
                    </Text>
                    <Button
                      size="xs"
                      colorScheme="blue"
                      variant="outline"
                      onClick={() => handleRegenerate(idx, 'caption')}
                      isLoading={p.isRegenerating?.caption}
                      loadingText="Regenerating..."
                      leftIcon={<RepeatIcon />}
                    >
                      Regenerate
                    </Button>
                  </HStack>
                  <CaptionEditor 
                    caption={p.caption}
                    onSave={(newCaption) => {
                      const updatedProgress = [...progress];
                      updatedProgress[idx].caption = newCaption;
                      updatedProgress[idx].cache_status = {
                        ...updatedProgress[idx].cache_status,
                        caption: false // User edited content is not from cache
                      };
                      setProgress(updatedProgress);
                    }}
                  />
                </Box>
              )}
              {p.imagePrompt && (
                <Box mt={4} p={4} borderWidth={1} borderRadius="md" bg="gray.50">
                  <HStack justify="space-between" mb={2}>
                    <Text fontWeight="bold">
                      Image Prompt:
                      {p.cache_status?.imagePrompt && (
                        <Text as="span" fontSize="sm" color="gray.500" ml={2}>
                          (from cache)
                        </Text>
                      )}
                    </Text>
                    <Button
                      size="xs"
                      colorScheme="blue"
                      variant="outline"
                      onClick={() => handleRegenerate(idx, 'imagePrompt')}
                      isLoading={p.isRegenerating?.imagePrompt}
                      loadingText="Regenerating..."
                      leftIcon={<RepeatIcon />}
                    >
                      Regenerate
                    </Button>
                  </HStack>
                  <Textarea
                    value={p.imagePrompt}
                    onChange={(e) => {
                      const updatedProgress = [...progress];
                      updatedProgress[idx].imagePrompt = e.target.value;
                      updatedProgress[idx].cache_status = {
                        ...updatedProgress[idx].cache_status,
                        imagePrompt: false // User edited content is not from cache
                      };
                      setProgress(updatedProgress);
                    }}
                    minH="100px"
                    size="sm"
                    bg="white"
                  />
                  <Box mt={4}>
                    {p.imageUrl ? (
                      <Box>
                        <img src={p.imageUrl} alt="Generated visual" style={{ maxWidth: '100%', borderRadius: 8, marginBottom: 8 }} />
                        <Button
                          size="xs"
                          colorScheme="teal"
                          variant="outline"
                          isLoading={p.isGeneratingImage}
                          loadingText="Generating..."
                          onClick={() => handleGenerateImageGPT(idx, true)}
                          mt={2}
                        >
                          Regenerate Image (GPT)
                        </Button>
                      </Box>
                    ) : (
                      <Button
                        size="xs"
                        colorScheme="teal"
                        variant="outline"
                        isLoading={p.isGeneratingImage}
                        loadingText="Generating..."
                        onClick={() => handleGenerateImageGPT(idx)}
                        mt={2}
                      >
                        Generate Image (GPT)
                      </Button>
                    )}
                  </Box>
                </Box>
              )}
            </Box>
          ))}
        </Box>
        {allDone && (
          <HStack spacing={4} mt={4} justify="center">
            {filename && (
              <Button
                as="a"
                href={`http://localhost:8000/download/${filename}`}
                colorScheme="blue"
                size="md"
                download
              >
                Download Word Document
              </Button>
            )}
            <Button
              colorScheme="pink"
              size="md"
              onClick={async () => {
                setIsPosting(true);
                try {
                  // Get all selected articles with their captions
                  const posts = progress
                    .filter(p => selectedForInstagram[p.article_link])
                    .map(p => ({
                      caption: p.caption,
                      article: {
                        title: p.title,
                        link: p.article_link
                      }
                    }));

                  // Post each one
                  for (const post of posts) {
                    await axios.post('http://localhost:8000/post_to_instagram', post);
                  }

                  toast({
                    title: `Posted ${posts.length} post${posts.length !== 1 ? 's' : ''} to Instagram!`,
                    status: 'success',
                    duration: 3000,
                    isClosable: true,
                  });
                } catch (error) {
                  console.error('Error posting to Instagram:', error);
                  toast({
                    title: 'Error posting to Instagram',
                    description: error.message,
                    status: 'error',
                    duration: 3000,
                    isClosable: true,
                  });
                  throw error;
                } finally {
                  setIsPosting(false);
                }
              }}
              isDisabled={!Object.values(selectedForInstagram).some(selected => selected)}
              isLoading={isPosting}
              loadingText="Posting..."
            >
              Post {Object.values(selectedForInstagram).filter(Boolean).length} to Instagram
            </Button>
          </HStack>
        )}

        <Modal isOpen={isOpen} onClose={onClose} size="xl">
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>Select Captions to Post</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <VStack spacing={4} align="stretch">
                {progress.map((p, idx) => (
                  <Box key={idx} borderWidth={1} p={4} borderRadius="md">
                    <Text fontWeight="bold" mb={2}>{p.title}</Text>
                    <Text mb={2} noOfLines={2}>{p.caption}</Text>
                    <Checkbox
                      isChecked={selectedForInstagram[p.article_link] || false}
                      onChange={(e) => {
                        setSelectedForInstagram(prev => ({
                          ...prev,
                          [p.article_link]: e.target.checked
                        }));
                      }}
                      colorScheme="pink"
                    >
                      Post this caption
                    </Checkbox>
                  </Box>
                ))}
              </VStack>
            </ModalBody>
            <ModalFooter>
              <Button colorScheme="blue" mr={3} onClick={onClose}>
                Close
              </Button>
              <Button 
                colorScheme="pink" 
                onClick={async () => {
                  const selectedCaptions = progress.filter(
                    p => selectedForInstagram[p.article_link]
                  );
                  
                  if (selectedCaptions.length === 0) {
                    toast({
                      title: 'No captions selected',
                      status: 'warning',
                      duration: 2000,
                      isClosable: true,
                    });
                    return;
                  }

                  try {
                    setIsPosting(true);
                    for (const item of selectedCaptions) {
                      await axios.post('http://localhost:8000/post_to_instagram', {
                        caption: item.caption,
                        article: {
                          title: item.title,
                          link: item.article_link
                        }
                      });
                    }
                    
                    toast({
                      title: 'Selected captions posted to Instagram!',
                      status: 'success',
                      duration: 3000,
                      isClosable: true,
                    });
                    onClose();
                  } catch (error) {
                    console.error('Error posting to Instagram:', error);
                    toast({
                      title: 'Error posting to Instagram',
                      description: error.message,
                      status: 'error',
                      duration: 3000,
                      isClosable: true,
                    });
                  } finally {
                    setIsPosting(false);
                  }
                }}
                isLoading={isPosting}
              >
                Post Selected to Instagram
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
        {error && (
          <Text color="red.500" mt={4}>{error}</Text>
        )}
      </Box>
    </Flex>
  );
}

export default App;