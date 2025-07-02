import React, { useState, useEffect, useRef } from 'react';
import { 
  Box, 
  Flex, 
  Button, 
  Text, 
  Spinner, 
  ChakraProvider, 
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
  Icon
} from '@chakra-ui/react';
import { RepeatIcon, ExternalLinkIcon } from '@chakra-ui/icons';
import { FaInstagram } from 'react-icons/fa';
import axios from 'axios';
import CaptionEditor from './components/CaptionEditor';

function App() {
  const [groupedArticles, setGroupedArticles] = useState([]); // [{feed_title, feed_url, articles: [{title, link, ...}]}]
  const [selected, setSelected] = useState([]); // [{feed_url, article_link}]
  const [progress, setProgress] = useState([]); // [{status, summary, caption, imagePrompt, feed_url, article_link, title}]
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [filename, setFilename] = useState(null);
  const [isPosting, setIsPosting] = useState(false);
  const [selectedForInstagram, setSelectedForInstagram] = useState({});
  const { isOpen, onOpen, onClose } = useDisclosure();
  const toast = useToast();
  const containerRef = useRef(null);

  // Fetch grouped RSS articles on load
  useEffect(() => {
    const fetchGrouped = async () => {
      try {
        const response = await axios.get('http://localhost:8000/get_rss_articles_grouped');
        setGroupedArticles(response.data);
      } catch (err) {
        setError('Failed to fetch grouped RSS articles.');
      }
    };
    fetchGrouped();
  }, []);

  // Handle selection
  const handleSelect = (feed_url, article_link, checked, title) => {
    if (checked) {
      setSelected(prev => [...prev, { feed_url, article_link, title }]);
    } else {
      setSelected(prev => prev.filter(s => !(s.feed_url === feed_url && s.article_link === article_link)));
    }
  };

  // Generate plan for selected articles
  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    setFilename(null);
    setProgress(selected.map(sel => ({ ...sel, status: 'pending', summary: '', caption: '', imagePrompt: '' })));
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
        newProgress[articleIdx].isRegenerating = {
          ...newProgress[articleIdx].isRegenerating,
          [type]: false
        };
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

  return (
    <Flex direction="column" align="center" justify="center" h="100vh" bg="gray.900">
      <Box
        ref={containerRef}
        bg="white"
        p={8}
        borderRadius={16}
        boxShadow="lg"
        minW="350px"
        textAlign="center"
        maxH="90vh"
        overflowY="auto"
      >
        <Text fontSize="2xl" fontWeight="bold" mb={4} color="teal.600">
          Dental Clinic Social Media Planner
        </Text>
        {groupedArticles.length > 0 && (
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
        )}
        <Button
          colorScheme="teal"
          size="lg"
          onClick={handleGenerate}
          isLoading={generating}
          loadingText="Generating..."
          mb={4}
        >
          Generate Content
        </Button>
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
                  >
                    Post to Instagram
                  </Checkbox>
                </HStack>
              </Box>
              {p.summary && (
                <Box mb={4} p={4} borderWidth={1} borderRadius="md" bg="gray.50">
                  <Text fontWeight="bold" mb={2}>Summary:</Text>
                  <Text>{p.summary}</Text>
                </Box>
              )}
              {p.caption && (
                <Box mt={4} p={4} borderWidth={1} borderRadius="md" bg="gray.50">
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