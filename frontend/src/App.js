import React, { useState, useEffect, useRef } from 'react';
import { Box, Flex, Button, Text, Spinner, ChakraProvider, Link, Checkbox, Progress, HStack, VStack, Divider } from '@chakra-ui/react';
import axios from 'axios';

function App() {
  const [groupedArticles, setGroupedArticles] = useState([]); // [{feed_title, feed_url, articles: [{title, link, ...}]}]
  const [selected, setSelected] = useState([]); // [{feed_url, article_link}]
  const [progress, setProgress] = useState([]); // [{status, summary, caption, imagePrompt, feed_url, article_link, title}]
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [filename, setFilename] = useState(null);
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
            const isSelected = selected.some(s => s.feed_url === feed.feed_url && s.article_link === article.link);
            if (isSelected) {
              newProgress.push({
                feed_url: feed.feed_url,
                article_link: article.link,
                title: article.title,
                status: 'done',
                summary: article.summary,
                caption: article.caption,
                imagePrompt: article.imagePrompt
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
                    <Checkbox
                      key={a.link}
                      isChecked={selected.some(s => s.feed_url === feed.feed_url && s.article_link === a.link)}
                      onChange={e => handleSelect(feed.feed_url, a.link, e.target.checked, a.title)}
                      mb={1}
                    >
                      <Link href={a.link} color="blue.500" isExternal>{a.title}</Link>
                    </Checkbox>
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
          disabled={generating || selected.length === 0}
        >
          Generate Plan
        </Button>
        <Box mt={4}>
          {progress.map((p, idx) => (
            <Box key={idx} mb={4} p={4} borderWidth={1} borderRadius={8} bg="gray.50" textAlign="left">
              <Text fontWeight="bold">
                <Link href={p.article_link} color="blue.500" isExternal>
                  {p.title}
                </Link>
              </Text>
              <Text>Status: {getStatusDisplay(p.status)}</Text>
              {p.summary && <Text mt={2}><b>Summary:</b> {p.summary}</Text>}
              {p.caption && <Text mt={2}><b>IG Caption:</b> {p.caption}</Text>}
              {p.imagePrompt && <Text mt={2}><b>Image Prompt:</b> {p.imagePrompt}</Text>}
            </Box>
          ))}
        </Box>
        {allDone && filename && (
          <Box mt={4}>
            <Button
              as="a"
              href={`http://localhost:8000/download/${filename}`}
              colorScheme="blue"
              size="md"
              download
            >
              Download Word Document
            </Button>
          </Box>
        )}
        {error && (
          <Text color="red.500" mt={4}>{error}</Text>
        )}
      </Box>
    </Flex>
  );
}

export default App;