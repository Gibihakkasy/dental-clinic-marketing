import { Text, Link } from '@chakra-ui/react';

// Regular expression to match URLs
const urlRegex = /(https?:\/\/[^\s]+)/g;

/**
 * Formats text with markdown-like syntax to HTML
 * @param {string} text - The text to format
 * @returns {string} Formatted HTML string
 */
export const formatText = (text) => {
  if (!text) return '';
  
  // Replace markdown headers with HTML
  let formatted = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Bold
    .replace(/\n\* /g, '\n• ');  // Convert markdown list to bullet points
    
  // Split into paragraphs (double newline)
  const paragraphs = formatted.split('\n\n');
  
  // Wrap each paragraph in <p> tags
  return paragraphs.map(paragraph => {
    // If it's a list, don't wrap in <p> tags
    if (paragraph.startsWith('•')) {
      return `<div>${paragraph.replace(/\n/g, '<br/>')}</div>`;
    }
    // If it's a header (ends with :), make it bold and add some margin
    if (paragraph.endsWith(':')) {
      return `<strong style="display: block; margin-top: 1em; margin-bottom: 0.5em;">${paragraph}</strong>`;
    }
    return `<p style="margin-bottom: 1em;">${paragraph}</p>`;
  }).join('');
};

/**
 * Renders formatted text with proper line breaks and styling
 * @param {string} text - The text to render
 * @returns {JSX.Element} Formatted text component
 */
export const FormattedText = ({ text }) => {
  if (!text) return null;
  
  // Split text into lines and process each line
  const lines = text.split('\n');
  
  // Function to process text and convert URLs to links
  const processTextWithLinks = (text) => {
    const parts = text.split(urlRegex);
    return parts.map((part, i) => {
      if (part.match(urlRegex)) {
        // Extract domain for display
        let displayText = part;
        try {
          const url = new URL(part);
          displayText = url.hostname.replace('www.', '');
        } catch (e) {
          // If URL parsing fails, use the original text
          console.error('Error parsing URL:', e);
        }
        
        return (
          <Link 
            key={i} 
            href={part} 
            isExternal
            color="blue.500"
            _hover={{ textDecoration: 'underline' }}
            title={part}
          >
            {displayText}
          </Link>
        );
      }
      return part;
    });
  };
  
  return (
    <div>
      {lines.map((line, index) => {
        // Check if line is a header (ends with :)
        if (line.endsWith(':')) {
          return (
            <Text key={`header-${index}`} fontWeight="bold" mt={4} mb={2}>
              {processTextWithLinks(line)}
            </Text>
          );
        }
        // Check if line is a list item (starts with - or •)
        if (line.trim().startsWith('- ') || line.trim().startsWith('• ')) {
          const bullet = line.trim().startsWith('- ') ? '-' : '•';
          const content = line.replace(/^[\-•]\s*/, '');
          
          return (
            <Text key={`list-${index}`} display="flex" alignItems="flex-start">
              <Text as="span" mr={2}>{bullet}</Text>
              <Text as="span">
                {processTextWithLinks(content)}
              </Text>
            </Text>
          );
        }
        // Regular paragraph
        return (
          <Text key={`para-${index}`} mb={2}>
            {processTextWithLinks(line)}
          </Text>
        );
      })}
    </div>
  );
};
