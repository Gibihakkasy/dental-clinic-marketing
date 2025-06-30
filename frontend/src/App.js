import React, { useState } from 'react';
import { Box, Flex, Button, Text, Spinner, ChakraProvider } from '@chakra-ui/react';
import axios from 'axios';

function App() {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [filename, setFilename] = useState(null);

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    setFilename(null);
    try {
      const response = await axios.post('http://localhost:8000/generate_social_plan', {});
      if (response.data && response.data.file) {
        setFilename(response.data.file);
      } else {
        setError('No file returned from backend.');
      }
    } catch (err) {
      setError('Error generating document: ' + (err.response?.data?.detail || err.message));
    } finally {
      setGenerating(false);
    }
  };

  return (
    <Flex direction="column" align="center" justify="center" h="100vh" bg="gray.900">
      <Box bg="white" p={8} borderRadius={16} boxShadow="lg" minW="350px" textAlign="center">
        <Text fontSize="2xl" fontWeight="bold" mb={4} color="teal.600">
          Dental Clinic Social Media Planner
        </Text>
        <Text mb={6} color="gray.700">
          Click the button below to generate a Word document with the latest dental news, summaries, Instagram captions, and image prompts.
        </Text>
        <Button
          colorScheme="teal"
          size="lg"
          onClick={handleGenerate}
          isLoading={generating}
          loadingText="Generating..."
          mb={4}
        >
          Generate Social Media Plan
        </Button>
        {filename && (
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